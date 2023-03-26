import os

import aiohttp
import discord
import yaml
from bs4 import BeautifulSoup
from discord.ext import commands


class CSMenuView(discord.ui.View):
    def __init__(self, menu_select):
        super().__init__(timeout=None)
        self.add_item(menu_select)

class CSMenu(discord.ui.Select):
    def __init__(self, csgo_cog, placeholder, options, current_level_values=None):
        if current_level_values:  
            options.append(discord.SelectOption(label="Back", value="Back"))
        super().__init__(placeholder=placeholder, options=options)
        self.cog = csgo_cog
        self.current_level_values = current_level_values or []

    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]
        value = selected_value.strip()

        if value == "Back":
            if not self.current_level_values:
                return  # Do nothing if there's no previous level

            self.current_level_values.pop()
            current_level_data = self.cog.data
            for level_value in self.current_level_values:
                current_level_data = current_level_data[level_value]

            options = await self.cog.create_select_options([str(item) for item in current_level_data.keys()])
            menu_select = CSMenu(self.cog, "Choose a category", options, self.current_level_values)
            menu_view = CSMenuView(menu_select)
            await interaction.response.edit_message(view=menu_view)
            return

        current_level_data = self.cog.data
        for level_value in self.current_level_values + [value]:
            current_level_data = current_level_data[level_value]

        if "fullName" in current_level_data:
            skin_name = current_level_data["fullName"]
            wear_prices, skin_image_url = await self.cog.fetch_skin_price(interaction, skin_name)
            if not hasattr(self, 'skin_embed_message'):
                self.skin_embed_message = await self.cog.send_skin_embed(interaction, skin_name, wear_prices, skin_image_url)
            else:
                await self.skin_embed_message.edit(embed=await self.cog.create_skin_embed(skin_name, wear_prices, skin_image_url))
            
            # Acknowledge the interaction to prevent the error message
            await interaction.response.defer()
            return


        options = await self.cog.create_select_options([str(item) for item in current_level_data.keys()])
        current_level_values = self.current_level_values + [value]
        menu_select = CSMenu(self.cog, f"Choose an option for {selected_value}", options, current_level_values)
        menu_view = CSMenuView(menu_select)
        await interaction.response.edit_message(view=menu_view)

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
                                skin_image_url = img_div["src"]

                        found_skin = True
                        break

                if not found_skin:
                    wear_prices[wear] = "N/A"

        return wear_prices, skin_image_url

    async def create_skin_embed(self, skin_name, wear_prices, skin_image_url):
        embed = discord.Embed(title=skin_name, color=discord.Color.blue())
        for wear, price in wear_prices.items():
            embed.add_field(name=wear, value=price, inline=True)
        embed.set_image(url=skin_image_url)
        return embed

    async def send_skin_embed(self, interaction, skin_name, wear_prices, skin_image_url):
        embed = discord.Embed(title=skin_name, color=discord.Color.blue())
        for wear, price in wear_prices.items():
            embed.add_field(name=wear, value=price, inline=True)
        embed.set_image(url=skin_image_url)

        return await interaction.channel.send(embed=embed)

    async def create_select_options(self, items):
        return [discord.SelectOption(label=item, value=item) for item in items if item]

    @discord.app_commands.command(name="skinprice", description="Get skin prices for CSGO")
    async def skinprice(self, interaction: discord.Interaction):
        top_level_options = await self.create_select_options(self.data.keys())
        menu_select = CSMenu(self, "Choose a category", top_level_options)
        await interaction.response.send_message("Select an option:", view=discord.ui.View().add_item(menu_select))

async def setup(bot):
    await bot.add_cog(CSGO(bot))