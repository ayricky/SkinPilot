import os
import json
import aiohttp
import discord
from bs4 import BeautifulSoup
from discord.ext import commands

class CSGOView(discord.ui.View):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot


class CSGO(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv('steam_key')

    async def fetch_csgo_items(self):
        with open("src/skin_data/skin_data.json") as file:
            return json.load(file)

    async def fetch_items_and_types(self):
        with open("src/skin_data/skin_data.json") as file:
            skin_data = json.load(file)
        # TODO: Parse JSON data

        return item_types


    async def fetch_skin_price(self, skin_name):
        wears = ["Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"]
        wear_prices = {}
        skin_image_url = None

        async with aiohttp.ClientSession() as session:
            for wear in wears:
                query = f"{skin_name} {wear}"
                url = f"https://steamcommunity.com/market/search/render/?query={query}&appid=730&key={self.api_key}"
                async with session.get(url) as response:
                    data = json.loads(await response.text())
                    if data["success"] and data["total_count"] > 0 and "results_html" in data:
                        soup = BeautifulSoup(data["results_html"], "html.parser")
                        listings = soup.find_all("a", class_="market_listing_row_link")

                        found_skin = False
                        for listing in listings:
                            listing_name = listing.find("span", class_="market_listing_item_name").text.strip()
                            if skin_name in listing_name and wear in listing_name:
                                price_div = listing.find("span", class_="sale_price")
                                if price_div:
                                    wear_prices[wear] = price_div.text.strip()

                                # Get the skin image URL
                                if not skin_image_url:
                                    img_div = listing.find("img", class_="market_listing_item_img")
                                    if img_div:
                                        skin_image_url = img_div["src"]

                                found_skin = True
                                break

                        if not found_skin:
                            wear_prices[wear] = "N/A"

        return wear_prices, skin_image_url



    def format_skin_data(self, skin_name, wear_prices, skin_image_url):
        embed = discord.Embed(title=f"Skin: {skin_name}")
        for wear, price in wear_prices.items():
            embed.add_field(name=wear, value=price, inline=True)

        if skin_image_url:
            embed.set_author(name=skin_name, icon_url=skin_image_url)

        return embed



    @commands.command()
    async def skinprice(self, ctx):
        item_data = await self.fetch_items_and_types()
        select_options = [
            discord.SelectOption(label=item_type, value=item_type) for item_type in item_data
        ]

        view = CSGOView(self.bot)
        view.add_item(ItemTypeSelectMenu(options=select_options, placeholder="Select an item type", max_values=1))

        embed = discord.Embed(title="Select a CS:GO item type to check prices", description="Choose an item type from the dropdown menu below.")
        await ctx.send(embed=embed, view=view)

    async def on_select_option(self, interaction):
        item_type = interaction.data["values"][0]

        if item_type == "Weapon Skins":
            gun_names = sorted(set(item["weapon"] for item in item_data["Weapons"]))

            select_options = [
                discord.SelectOption(label=gun_name, value=gun_name) for gun_name in gun_names
            ]
            select_options.append(discord.SelectOption(label="Back", value="back"))  # Add the "Back" option here

            view = CSGOView(self.bot)
            view.add_item(GunSelectMenu(options=select_options, placeholder="Select a gun", max_values=1))

            embed = discord.Embed(title="Select a CS:GO gun to check skin prices", description="Choose a gun from the dropdown menu below.")
            await interaction.response.send_message(embed=embed, view=view)



class ItemTypeSelectMenu(discord.ui.Select):
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "back":
            await self.view.bot.get_cog("CSGO").skinprice(interaction)
            return

        await interaction.message.delete()
        await self.view.bot.get_cog("CSGO").on_select_option(interaction)

class GunSelectMenu(discord.ui.Select):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "back":
            await self.view.bot.get_cog("CSGO").skinprice(interaction)
            return

        await interaction.message.delete()
        gun_name = interaction.data["values"][0]

        skins_data = await self.view.bot.get_cog("CSGO").fetch_skin_names()
        skin_names = sorted(skin["name"] for skin in skins_data if skin["weapon"] == gun_name)

        select_options = [
            discord.SelectOption(label=skin_name, value=skin_name) for skin_name in skin_names
        ]
        select_options.append(discord.SelectOption(label="Back", value="back"))

        view = CSGOView(self.view.bot)
        view.add_item(SkinSelectMenu(options=select_options, placeholder="Select a skin", max_values=1))

        embed = discord.Embed(title=f"Select a {gun_name} skin to check prices", description="Choose a skin from the dropdown menu below.")
        await interaction.response.send_message(embed=embed, view=view)

class SkinSelectMenu(discord.ui.Select):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "back":
            await self.view.bot.get_cog("CSGO").on_select_option(interaction)
            return

        await interaction.response.defer()

        skin_name = self.values[0]
        wear_prices, skin_image_url = await self.view.bot.get_cog("CSGO").fetch_skin_price(skin_name)
        if wear_prices:
            embed = self.view.bot.get_cog("CSGO").format_skin_data(skin_name, wear_prices, skin_image_url)
            await interaction.edit_original_response(embed=embed)
        else:
            await interaction.edit_original_response(content=f"No results found for '{skin_name}'")

async def setup(bot):
    await bot.add_cog(CSGO(bot))
