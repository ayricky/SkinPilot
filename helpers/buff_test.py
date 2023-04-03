import asyncio

import aiohttp


async def fetch_buff_and_steam_skin_data(item_id):
    url = f"https://buff.163.com/api/market/goods/sell_order?game=csgo&goods_id={item_id}&page_num=1&sort_by=default&mode=&allow_tradable_cooldown=1"

    max_retries = 5
    backoff_factor = 2

    for attempt in range(1, max_retries + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
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

                breakpoint()
                skin_image_url = data["data"]["goods_infos"][str(item_id)]["original_icon_url"]
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


async def main():
    buff_price, steam_price, skin_image_url = await fetch_buff_and_steam_skin_data(42389)
    print("Buff price:", buff_price)
    print("Steam price:", steam_price)
    print("Skin image URL:", skin_image_url)


if __name__ == "__main__":
    asyncio.run(main())
