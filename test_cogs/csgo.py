import asyncio
import io
import os
import sqlite3

import discord
import matplotlib.pyplot as plt
from discord import ButtonStyle, app_commands
from discord.ext import commands
from fuzzywuzzy import process


class CSGO(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv("steam_key")
        self.conn = self.init_db_connection("data/csgo_items.db")
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT name FROM items")
            self.all_skin_names = [row["name"] for row in cursor.fetchall()]

    def init_db_connection(self, db_path):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def fetch_buff_and_steam_skin_data(self, interaction, item_id):
        url = f"https://buff.163.com/api/market/goods/sell_order?game=csgo&goods_id={item_id}&page_num=1&sort_by=default&mode=&allow_tradable_cooldown=1"

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

    async def fetch_skin_data_for_item_record(self, interaction, item_record):
        wear = item_record["wear"]
        is_stattrak = item_record["is_stattrak"]
        is_souvenir = item_record["is_souvenir"]
        buff_item_id = item_record["buff_id"]

        buff_price, steam_price, skin_image_url = await self.fetch_buff_and_steam_skin_data(interaction, buff_item_id)

        return {
            "wear_label": wear,
            "buff_price": buff_price,
            "steam_price": steam_price,
            "skin_image_url": skin_image_url,
            "is_stattrak": is_stattrak,
            "is_souvenir": is_souvenir,
            "raw_name": item_record["raw_name"].replace(f"({wear})", ""),
        }

    async def create_price_table_image(self, wear_prices):
        wears, buff_prices, steam_prices = zip(
            *[
                (
                    wp["wear_label"],
                    float(wp["buff_price"].replace("$", "")) if wp["buff_price"] != "N/A" else 0,
                    float(wp["steam_price"].replace("$", "")) if wp["steam_price"] != "N/A" else 0,
                )
                for wp in wear_prices
            ]
        )

        fig, ax = plt.subplots()
        ax.bar(wears, buff_prices, label="Buff Price", alpha=0.6)
        ax.bar(wears, steam_prices, label="Steam Price", alpha=0.6)
        ax.set_ylabel("Price (USD)")
        ax.set_title("Skin Prices")
        ax.legend()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close(fig)

        return buf

    @app_commands.command(name="skinp", description="Get skin prices for CSGO 2")
    async def skinp(self, interaction: discord.Interaction, item: str):
        await interaction.response.defer()

        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT raw_name, buff_id, wear, is_stattrak, is_souvenir FROM items WHERE name = ?", (item,)
            )
            valid_items = cursor.fetchall()

        if not valid_items:
            await interaction.followup.send("Invalid item. Please enter a valid item name.")
            return

        tasks = [self.fetch_skin_data_for_item_record(interaction, item_record) for item_record in valid_items]
        wear_prices = await asyncio.gather(*tasks)

        filtered_wear_prices = [
            wear_price for wear_price in wear_prices if not (wear_price["is_stattrak"] or wear_price["is_souvenir"])
        ]
        table_image_buffer = await self.create_price_table_image(filtered_wear_prices)

        skin_image = discord.File(table_image_buffer, filename="skin_prices.png")
        buttons = SkinButtons(wear_prices, item, self)

        await interaction.followup.send(file=skin_image, view=buttons)

    @skinp.autocomplete(name="item")
    async def skin_autocomplete(self, inter: discord.Interaction, value: str):
        if value == "":
            common_high_tier = ["AWP | Dragon Lore", "AK-47 | Wild Lotus", "AK-47 | Gold Arabesque"]
            return [app_commands.Choice(name=skin, value=skin) for skin in common_high_tier]

        suggestions = process.extract(value, self.all_skin_names, limit=25)
        suggestions = [app_commands.Choice(name=skin, value=skin) for skin, _ in suggestions if _ > 70]

        return suggestions


class ToggleButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        self.style = ButtonStyle.green if self.style == ButtonStyle.grey else ButtonStyle.grey
        await self.view.update_skin_and_table(interaction)


class SkinButtons(discord.ui.View):
    def __init__(self, wear_prices, skin_name, cog):
        super().__init__()
        self.wear_prices = wear_prices
        self.skin_name = skin_name
        self.cog = cog

        self.buttons = {
            "souvenir": ToggleButton(style=discord.ButtonStyle.grey, label="Souvenir", custom_id="souvenir"),
            "stattrak": ToggleButton(style=discord.ButtonStyle.grey, label="StatTrak™", custom_id="stattrak"),
        }
        for button in self.buttons.values():
            self.add_item(button)

        # Initialize wear_buttons as an empty dictionary
        self.wear_buttons = {}

        self.wear_buttons = {
            wear_price["wear_label"]: ToggleButton(
                style=discord.ButtonStyle.grey,
                label=wear_price["wear_label"],
                custom_id=f"wear_{wear_price['wear_label']}",
            )
            for wear_price in wear_prices
            if wear_price["wear_label"] not in self.wear_buttons
        }
        for wear_button in self.wear_buttons.values():
            self.add_item(wear_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True

    async def update_skin_and_table(self, interaction):
        active_buttons = [button for button in self.children if button.style == ButtonStyle.green]

        filtered_wear_prices = self.wear_prices
        if self.buttons["souvenir"] in active_buttons:
            filtered_wear_prices = [wear_price for wear_price in filtered_wear_prices if wear_price["is_souvenir"]]
        if self.buttons["stattrak"] in active_buttons:
            filtered_wear_prices = [wear_price for wear_price in filtered_wear_prices if wear_price["is_stattrak"]]
        if not filtered_wear_prices:
            filtered_wear_prices = [
                wear_price
                for wear_price in self.wear_prices
                if not (wear_price["is_stattrak"] or wear_price["is_souvenir"])
            ]

        skin_image_url = filtered_wear_prices[0]["skin_image_url"]
        table_image = self.create_price_table_image(filtered_wear_prices)
        table_image_url = await self.cog.upload_image(interaction, table_image)

        await interaction.response.edit_message(content=f"{self.skin_name}\n{skin_image_url}\n{table_image_url}")


async def setup(bot):
    await bot.add_cog(CSGO(bot))
