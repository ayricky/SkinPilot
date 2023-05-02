import asyncio

from urllib.parse import urlencode

def fetch_buff_w_options(
        interaction,
        item_id,
        # Default
        sort_by = None,
        # Float Range
        min_paintwear = None,
        max_paintwear = None,
        # Style filter
        tags_id = None,
        # Name Tag
        name_tag = None,
        # Stickers
        extra_tag_id = None,
        # Paint seed
        paintseed_group = None,
        paintseed = None,
        tier = None,
        # Fade Range
        min_fade = None,
        max_fade = None,
        # Applied Patches
        extra_tag_ids = None,
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

    # Build the URL
    url = f"https://buff.163.com/api/market/goods/sell_order?{query_string}"

    return fetch_buff_data(interaction, item_id, url)

async def fetch_buff_data(interaction, item_id, url):
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
                steam_price = data["data"]["goods_infos"][str(item_id)]["steam_price"]
                steam_price_cny = data["data"]["goods_infos"][str(item_id)]["steam_price_cny"]
                buff_price = float(data["data"]["items"][0]["price"])

                if steam_price_cny and steam_price:
                    conversion_rate = float(steam_price) / float(steam_price_cny)
                    buff_price_usd = buff_price * conversion_rate
                else:
                    buff_price_usd = "N/A"

                skin_image_url = None

                for item in data["data"]["items"]:
                    if (
                        "asset_info" in item
                        and "info" in item["asset_info"]
                        and "inspect_en_url" in item["asset_info"]["info"]
                    ):
                        skin_image_url = item["asset_info"]["info"]["inspect_en_url"]
                        break

                return (
                    f"${buff_price_usd:.2f}" if isinstance(buff_price_usd, float) else "N/A",
                    steam_price,
                    skin_image_url,
                )
            else:
                return "N/A", "N/A", None

        except Exception as e:
            if attempt == max_retries:
                raise e
            else:
                wait_time = backoff_factor**attempt
                await asyncio.sleep(wait_time)
                continue


def get_item_data(conn, item, wear=None):
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            """
    SELECT i.raw_name, i.buff_id, i.wear, i.is_stattrak, i.is_souvenir
    FROM items i
    WHERE i.name = ?
    """,
            (item,),
        )
        return cursor.fetchone()

