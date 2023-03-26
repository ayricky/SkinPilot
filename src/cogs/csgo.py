import json
import os
import random
from difflib import SequenceMatcher

import discord
from bs4 import BeautifulSoup
from discord import app_commands
from discord.ext import commands


class CSGO(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv('steam_key')
        self.WEARS = ["Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"]
        with open('data/skin_data/full_names.json', 'r') as file:
            self.data = json.load(file)

    async def fetch_wear_data(self, bot, skin_name, wear):
        query = f"{skin_name} {wear}"
        url = f"https://steamcommunity.com/market/search/render/?query={query}&appid=730&key={self.api_key}"
        async with bot.session.get(url) as response:
            return await response.json()

    async def fetch_skin_price(self, interaction, skin_name):
        wear_prices = {}
        skin_image_url = None

        for wear in self.WEARS:
            data = await self.fetch_wear_data(interaction.client, skin_name, wear)

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

                        if not skin_image_url:
                            img_div = listing.find("img", class_="market_listing_item_img")
                            if img_div:
                                small_image_url = img_div["src"]
                                # Replace the thumbnail URL with the larger version
                                skin_image_url = small_image_url.replace('/62fx62f', '/512fx512f')

                        found_skin = True
                        break

                if not found_skin:
                    wear_prices[wear] = "N/A"

        return wear_prices, skin_image_url

    async def create_skin_embed(self, skin_name, wear_prices, skin_image_url):
        color = discord.Color(random.randint(0, 0xFFFFFF))
        embed = discord.Embed(title=skin_name, color=color)
        for wear, price in wear_prices.items():
            embed.add_field(name=wear, value=price, inline=True)
        embed.set_image(url=skin_image_url)
        return embed


    @app_commands.command(name="skinprice", description="Get skin prices for CSGO")
    async def skinprice(self, interaction: discord.Interaction, item: str):
        valid_items = [skin for skin in self.data if skin == item]

        if not valid_items:
            await interaction.response.send_message("Invalid item. Please enter a valid item name.")
            return

        skin_name = valid_items[0]
        wear_prices, skin_image_url = await self.fetch_skin_price(interaction, skin_name)
        embed = await self.create_skin_embed(skin_name, wear_prices, skin_image_url)
        await interaction.response.send_message(embed=embed)

    @skinprice.autocomplete(name="item")
    async def skin_autocomplete(self, inter: discord.Interaction, value: str):
        def match_characters_in_order(value, skin):
            value_index, skin_index = 0, 0
            while value_index < len(value) and skin_index < len(skin):
                if value[value_index] == skin[skin_index]:
                    value_index += 1
                skin_index += 1
            return value_index == len(value)

        value = value.lower()
        suggestions = [skin for skin in self.data if match_characters_in_order(value, skin.lower())]

        # sort the suggestions by similarity to the search value
        suggestions = sorted(suggestions, key=lambda x: SequenceMatcher(None, value, x.lower()).ratio(), reverse=True)

        suggestions = suggestions[:25]
        suggestions = [app_commands.Choice(name=skin, value=skin) for skin in suggestions]

        return suggestions

async def setup(bot):
    await bot.add_cog(CSGO(bot))
