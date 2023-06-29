import asyncio
from urllib.parse import urlencode

from sqlalchemy.orm import Session
from models.item import Item


def construct_buff_url(
    item_id,
    # Default
    sort_by=None,
    # Float Range
    min_paintwear=None,
    max_paintwear=None,
    # Style filter
    tags_id=None,
    # Name Tag
    name_tag=None,
    # Stickers
    extra_tag_id=None,
    # Paint seed
    paintseed_group=None,
    paintseed=None,
    tier=None,
    # Fade Range
    min_fade=None,
    max_fade=None,
    # Applied Patches
    extra_tag_ids=None,
):
    # Create a dictionary with the URL parameters
    params = {
        "game": "csgo",
        "goods_id": item_id,
        "sort_by": sort_by,
        "min_paintwear": min_paintwear,
        "max_paintwear": max_paintwear,
        "tags_id": tags_id,
        "name_tag": name_tag,
        "extra_tag_id": extra_tag_id,
        "paintseed_group": paintseed_group,
        "paintseed": paintseed,
        "tier": tier,
        "min_fade": min_fade,
        "max_fade": max_fade,
        "extra_tag_ids": extra_tag_ids,
    }

    # Remove keys with None values
    params = {k: v for k, v in params.items() if v is not None}

    # Convert the dictionary to a URL-encoded query string
    query_string = urlencode(params)

    return f"https://buff.163.com/api/market/goods/sell_order?{query_string}"


async def fetch_buff_data(interaction, item_id, url=None):
    if url is None:
        url = f"https://buff.163.com/api/market/goods/sell_order?game=csgo&goods_id={item_id}"

    max_retries = 5
    backoff_factor = 2

    for attempt in range(1, max_retries + 1):
        try:
            async with interaction.client.session.get(url) as response:
                if response.status == 429:
                    raise Exception("Rate limited")
                response.raise_for_status()
                data = await response.json()

            if data["code"] == "OK" and data["data"]["total_count"] > 0:
                return data

        except Exception as e:
            if attempt == max_retries:
                raise e
            else:
                wait_time = backoff_factor**attempt
                await asyncio.sleep(wait_time)
                continue


def get_first_item_data(data, item_id):
    steam_price = data["data"]["goods_infos"][str(item_id)]["steam_price"]
    steam_price_cny = data["data"]["goods_infos"][str(item_id)]["steam_price_cny"]
    buff_price = float(data["data"]["items"][0]["price"])
    conversion_rate = float(steam_price) / float(steam_price_cny)
    buff_price_usd = buff_price * conversion_rate
    steam_price = steam_price if steam_price < 2000 else "N/A"

    base_image = data["data"]["goods_infos"][str(item_id)]["original_icon_url"]
    for item in data["data"]["items"]:
        if "asset_info" in item and "info" in item["asset_info"] and "inspect_en_url" in item["asset_info"]["info"]:
            skin_image_url = item["asset_info"]["info"]["inspect_en_url"]
            break
        else:
            skin_image_url = base_image

    parsed_data = [
        {
            item_id: {
                buff_price: f"{buff_price_usd:.2f}",
                steam_price: steam_price,
                skin_image_url: skin_image_url,
                base_image: base_image,
            }
        }
    ]

    return parsed_data


def get_all_relevant_items(session: Session, item: str):
    items = session.query(Item).filter(Item.name == item).all()

    # Separate items into regular, StatTrak, and Souvenir lists
    regular_items = []
    stattrak_items = []
    souvenir_items = []
    item_type = None

    for item in items:
        if item.is_stattrak:
            stattrak_items.append(item)
        elif item.is_souvenir:
            souvenir_items.append(item)
        else:
            regular_items.append(item)

        if item_type is None:
            item_type = item.item_type

    return {
        "item_type": item_type,
        "regular_items": regular_items,
        "stattrak_items": stattrak_items,
        "souvenir_items": souvenir_items,
    }

async def fetch_all_item_data(interaction, session: Session, item: str, stattrak=False, souvenir=False, *args, **kwargs):
    cs_items = get_all_relevant_items(session, item)

    item_data_list = []
    for item in cs_items["regular_items"] + cs_items["stattrak_items"] + cs_items["souvenir_items"]:
        item_id = item.buff_id

        # Construct the URL using the passed arguments
        url = construct_buff_url(item_id, *args, **kwargs)

        # Fetch data using the constructed URL
        data = await fetch_buff_data(interaction, item_id, url=url)

        # Get the first item data
        first_item_data = get_first_item_data(data, item_id)

        item_data_list.append((item, first_item_data))

    return item_data_list
