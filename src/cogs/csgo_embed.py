import asyncio
import os
import random
import sqlite3

import discord
from discord import ButtonStyle, app_commands
from discord.ext import commands


class CSGO(commands.Cog):
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

    async def fetch_skin_data_for_item_record(self, interaction, item_record):
        wear = item_record["wear"]
        is_stattrak = item_record["is_stattrak"]
        is_souvenir = item_record["is_souvenir"]
        buff_item_id = item_record["buff_id"]

        buff_price, steam_price, skin_image_url = await self.fetch_buff_data(interaction, buff_item_id)

        return {
            "wear_label": wear,
            "buff_price": buff_price,
            "steam_price": steam_price,
            "skin_image_url": skin_image_url,
            "is_stattrak": is_stattrak,
            "is_souvenir": is_souvenir,
            "raw_name": item_record["raw_name"].replace(f"({wear})", ""),
        }

    async def create_skin_embed(self, wear_prices):
        skin_name = wear_prices[0]["raw_name"]
        skin_image_url = wear_prices[0]["skin_image_url"]
        color = discord.Color(random.randint(0, 0xFFFFFF))
        embed = discord.Embed(title=skin_name, color=color)
        embed.set_image(url=skin_image_url)

        table_header = "Wear           | Buff Price  | Steam Price\n"
        table_separator = "---------------|-------------|------------\n"
        table_rows = ""

        wear_order = {"Factory New": 0, "Minimal Wear": 1, "Field-Tested": 2, "Well-Worn": 3, "Battle-Scarred": 4}
        wear_prices.sort(key=lambda wear_price: wear_order[wear_price["wear_label"]])

        for wear_price in wear_prices:
            wear_label = wear_price["wear_label"]
            buff_price = wear_price["buff_price"]
            steam_price = (
                f"${float(wear_price['steam_price']):,.2f}"
                if wear_price["steam_price"]
                and wear_price["steam_price"] != "N/A"
                and float(wear_price["steam_price"]) < 2000
                else "N/A"
            )

            table_rows += f"{wear_label:<15}| {buff_price:<12}| {steam_price}\n"

        table = f"```{table_header}{table_separator}{table_rows}```"
        embed.description = table

        return embed

    @app_commands.command(name="skinprice", description="Get skin prices for CSGO")
    async def skinprice(self, interaction: discord.Interaction, item: str):
        await interaction.response.defer(thinking=True)

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
        embed = await self.create_skin_embed(filtered_wear_prices)

        buttons = SkinButtons(wear_prices, item, self)

        if buttons.children:
            await interaction.followup.send(embed=embed, view=buttons)
        else:
            await interaction.followup.send(embed=embed)

    @skinprice.autocomplete(name="item")
    async def skin_autocomplete(self, inter: discord.Interaction, value: str):
        if value == "":
            common_high_tier = ["AWP | Dragon Lore", "AK-47 | Wild Lotus", "AK-47 | Gold Arabesque"]
            return [app_commands.Choice(name=skin, value=skin) for skin in common_high_tier]

        suggestions = [app_commands.Choice(name=skin, value=skin) for skin in self.all_skin_names if value.lower() in skin.lower()][:25]

        return suggestions


class SkinButton(discord.ui.Button):
    def __init__(self, custom_id, label, style, item_type, parent_view):
        super().__init__(label=label, custom_id=custom_id, style=style)
        self.item_type = item_type
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if self.item_type in self.parent_view.wear_order:  # Check if the button is a wear button
            for button in self.parent_view.children:
                if button.item_type in self.parent_view.wear_order:  # Check if the button is a wear button
                    button.style = ButtonStyle.grey  # Set all wear buttons to grey
            self.style = ButtonStyle.blurple  # Set the clicked wear button to blurple
        elif self.item_type == "souvenir" or self.item_type == "stattrak":
            for button in self.parent_view.children:
                if (
                    button.item_type == "souvenir" or button.item_type == "stattrak"
                ) and button != self:  # Deselect the other type
                    button.style = ButtonStyle.grey
            if self.style == ButtonStyle.grey:  # Toggle button on
                self.style = ButtonStyle.green
            else:  # Toggle button off
                self.style = ButtonStyle.grey

        active_buttons = [
            button
            for button in self.parent_view.children
            if button.style == ButtonStyle.green or button.style == ButtonStyle.blurple
        ]
        filtered_wear_prices = self.parent_view.get_filtered_wear_prices(active_buttons)
        embed = await self.parent_view.cog.create_skin_embed(filtered_wear_prices)
        skin_image_url = filtered_wear_prices[0]["skin_image_url"] if filtered_wear_prices else None
        await interaction.response.edit_message(embed=embed, view=self.parent_view)
        await self.parent_view.send_image(interaction, skin_image_url, embed)


class SkinButtons(discord.ui.View):
    def __init__(self, wear_prices, skin_name, cog):
        super().__init__()
        self.wear_prices = wear_prices
        self.skin_name = skin_name
        self.cog = cog

        self.skin_types = {
            "souvenir": {
                "exists": any(wear_price["is_souvenir"] for wear_price in wear_prices),
                "label": "Souvenir",
                "style": discord.ButtonStyle.grey,
            },
            "stattrak": {
                "exists": any(wear_price["is_stattrak"] for wear_price in wear_prices),
                "label": "StatTrak™",
                "style": discord.ButtonStyle.grey,
            },
        }

        self.wear_order = ["Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"]

        # Add buttons for wear
        self.wear_types = set(wear_price["wear_label"] for wear_price in wear_prices)
        for wear in self.wear_order:
            if wear in self.wear_types:
                custom_id = f"wear_{wear}"
                style = discord.ButtonStyle.grey
                self.add_item(SkinButton(custom_id, wear, style, wear, self))

        # Set the highest priority wear button as blurple by default
        highest_priority_wear = min(self.wear_types, key=lambda wear: self.wear_order.index(wear))
        highest_priority_button = next(button for button in self.children if button.item_type == highest_priority_wear)
        highest_priority_button.style = ButtonStyle.blurple

        # Add Souvenir and StatTrak buttons if they exist
        for skin_type, skin_data in self.skin_types.items():
            if skin_data["exists"]:
                custom_id = f"{skin_type}"
                label = skin_data["label"]
                style = skin_data["style"]
                self.add_item(SkinButton(custom_id, label, style, skin_type, self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True

    def get_filtered_wear_prices(self, active_buttons):
        if not active_buttons:  # If no buttons are active, show the original embed
            return [
                wear_price
                for wear_price in self.wear_prices
                if not (wear_price["is_stattrak"] or wear_price["is_souvenir"])
            ]

        filtered_wear_prices = []
        for wear_price in self.wear_prices:
            stattrak_active = any(btn.item_type == "stattrak" for btn in active_buttons)
            souvenir_active = any(btn.item_type == "souvenir" for btn in active_buttons)
            wear_active = any(btn.item_type == wear_price["wear_label"] for btn in active_buttons)

            if (
                (not stattrak_active and not souvenir_active)
                or (stattrak_active and wear_price["is_stattrak"])
                or (souvenir_active and wear_price["is_souvenir"])
            ) and wear_active:
                filtered_wear_prices.append(wear_price)

        return filtered_wear_prices

    async def send_image(self, interaction, skin_image_url, embed):
        if skin_image_url:
            embed.set_image(url=skin_image_url)
        else:
            highest_priority_wear = min(self.wear_types, key=lambda wear: self.wear_order.index(wear))
            default_skin = next(
                wear_price for wear_price in self.wear_prices if wear_price["wear_label"] == highest_priority_wear
            )
            embed.set_image(url=default_skin["skin_image_url"])
        await interaction.edit_original_message(embed=embed, view=self)


async def setup(bot):
    await bot.add_cog(CSGO(bot))
