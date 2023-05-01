import asyncio
import sqlite3

import discord
from discord import app_commands
from discord.ext import commands


class CS2SkinPrice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = self.init_db_connection("data/cs_items.db")
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT name FROM items")
            self.all_skin_names = [row["name"] for row in cursor.fetchall()]

    def init_db_connection(self, db_path):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def fetch_buff_data(self, interaction, item_id):
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

    def get_item_data(self, item):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(
                '''
                SELECT i.raw_name, i.buff_id, i.wear, i.is_stattrak, i.is_souvenir, b.*
                FROM items i
                JOIN buff163 b ON i.buff_id = b.buff_id
                WHERE i.name = ?
                ''', (item,)
            )
            return cursor.fetchall()


    @app_commands.command(name="pricecheck", description="Get skin prices for CS2 items")
    async def pricecheck(self, interaction: discord.Interaction, item: str):
        await interaction.response.defer(thinking=True)

        item_data = self.get_item_data(item)

        if item_data is None:
            await interaction.followup.send("Invalid item. Please enter a valid item name.")
            return

        buff_price_usd, steam_price, skin_image_url = await self.fetch_buff_data(interaction, item_data["buff_id"])

        if skin_image_url:
            embed = discord.Embed(title=f"{item}", description=f"Buff Price: {buff_price_usd}\nSteam Price: {steam_price}")
            embed.set_image(url=skin_image_url)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"{item}\nBuff Price: {buff_price_usd}\nSteam Price: {steam_price}")


    @pricecheck.autocomplete(name="item")
    async def pricecheck_autocomplete(self, interaction: discord.Interaction, value: str):
        if value == "":
            common_high_tier = ["AWP | Dragon Lore", "AK-47 | Wild Lotus", "AK-47 | Gold Arabesque"]
            return [app_commands.Choice(name=skin, value=skin) for skin in common_high_tier]

        suggestions = [app_commands.Choice(name=skin, value=skin) for skin in self.all_skin_names if value.lower() in skin.lower()][:25]

        return suggestions


async def setup(bot):
    await bot.add_cog(CS2SkinPrice(bot))