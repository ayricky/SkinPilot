import sqlite3

import discord
from discord import app_commands
from discord.ext import commands
import utils.buff163_utils as buff_utils


class CS2SkinPrice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = self.init_db_connection("data/cs_items.db")
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT name FROM items")
            self.all_item_names = [row["name"] for row in cursor.fetchall()]

    def init_db_connection(self, db_path):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @app_commands.command(name="pricecheck", description="Get skin prices for CS2 items")
    async def pricecheck(self, interaction: discord.Interaction, item: str):
        await interaction.response.defer(thinking=True)

        if item not in self.all_item_names:
            await interaction.followup.send("Invalid item. Please enter a valid item name.")
            return
        
        # item_data = buff_utils.get_item_data(self.conn, item)
        item_data = buff_utils.fetch_all_item_data(interaction, self.conn, item)

        buff_price_usd, steam_price, skin_image_url = await buff_utils.fetch_buff_w_options(
            interaction, item_data["buff_id"]
        )

        if skin_image_url:
            embed = discord.Embed(
                title=f"{item}", description=f"Buff Price: {buff_price_usd}\nSteam Price: {steam_price}"
            )
            embed.set_image(url=skin_image_url)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"{item}\nBuff Price: {buff_price_usd}\nSteam Price: {steam_price}")

    @pricecheck.autocomplete(name="item")
    async def pricecheck_autocomplete(self, interaction: discord.Interaction, value: str):
        if value == "":
            common_high_tier = ["AWP | Dragon Lore", "AK-47 | Wild Lotus", "AK-47 | Gold Arabesque"]
            return [app_commands.Choice(name=skin, value=skin) for skin in common_high_tier]

        suggestions = [
            app_commands.Choice(name=skin, value=skin) for skin in self.all_item_names if value.lower() in skin.lower()
        ][:25]

        return suggestions


async def setup(bot):
    await bot.add_cog(CS2SkinPrice(bot))