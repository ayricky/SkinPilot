import os
import random

import discord
import yaml
from bs4 import BeautifulSoup
from discord.ext import commands


class CSMenu(discord.ui.Select):
    def __init__(self, csgo_cog, placeholder, options, items_per_page=22, current_level_values=None):
        self._options = options
        self.items_per_page = items_per_page
        self.current_page = 0
        self.current_level_values = current_level_values or []
        self.cog = csgo_cog
        options_to_display = self.get_options_to_display()
        super().__init__(placeholder=placeholder, options=options_to_display)

    def get_options_to_display(self):
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        options_to_display = self._options[start:end]

        if self.current_level_values:
            options_to_display.append(discord.SelectOption(label="Back", value="Back"))

        options_to_display.append(discord.SelectOption(label="Previous Page", value="Previous Page", disabled=self.current_page == 0))

        options_to_display.append(discord.SelectOption(label="Next Page", value="Next Page", disabled=(self.current_page + 1) * self.items_per_page >= len(self._options)))

        return options_to_display

    def update_options(self):
        self.options = self.get_options_to_display()

    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]
        value = selected_value.strip()

        if value == "Back":
            if not self.current_level_values:
                return

            self.current_level_values.pop()
        elif value == "Next Page":
            self.current_page += 1
        elif value == "Previous Page":
            self.current_page -= 1
        else:
            self.current_level_values.append(value)

        current_level_data = self.cog.data
        for level_value in self.current_level_values:
            current_level_data = current_level_data[level_value]

        if "fullName" in current_level_data:
            skin_name = current_level_data["fullName"]
            wear_prices, skin_image_url = await self.cog.fetch_skin_price(interaction, skin_name)
            skin_embed = await self.cog.create_skin_embed(skin_name, wear_prices, skin_image_url)
            await interaction.channel.send(embed=skin_embed)

            await interaction.response.defer()
            return

        self.options = await self.cog.create_select_options([str(item) for item in current_level_data.keys()])
        self.update_options()
        await interaction.response.edit_message(view=self.view)

class CSGO(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv('steam_key')
        self.WEARS = ["Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"]
        with open('data/skin_data/filtered_skin_data.yaml') as file:
            self.data = yaml.safe_load(file)

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
        color = discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        embed = discord.Embed(title=skin_name, color=color)
        for wear, price in wear_prices.items():
            embed.add_field(name=wear, value=price, inline=True)
        embed.set_image(url=skin_image_url)
        return embed

    async def create_select_options(self, items):
        return [discord.SelectOption(label=item, value=item) for item in items if item]

    @discord.app_commands.command(name="skinprice", description="Get skin prices for CSGO")
    async def skinprice(self, interaction: discord.Interaction):
        top_level_options = await self.create_select_options(self.data.keys())
        menu_select = CSMenu(self, "Choose a category", top_level_options)
        await interaction.response.send_message("Select an option:", view=discord.ui.View().add_item(menu_select))

async def setup(bot):
    await bot.add_cog(CSGO(bot))
