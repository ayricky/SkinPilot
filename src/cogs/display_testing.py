import discord
from discord import Button, ButtonStyle, SelectOption, app_commands
from discord.ui import Select
from discord.ext import commands

class DataDisplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_embed_with_data(self, interaction, title, image_url, components=None):
        embed = discord.Embed(title=title)
        embed.set_image(url=image_url)
        embed.add_field(name="Price Data", value="Price 1: $100\nPrice 2: $200\nPrice 3: $300", inline=False)
        await interaction.response.send_message(content="Here's the data with different UI components:", embed=embed, components=components, ephemeral=True)

    @app_commands.command(name="buttons", description="Display Embed with buttons")
    async def buttons(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Buttons Example", description="Click a button to see its response.")
        view = discord.ui.View()

        view.add_item(Button(ButtonStyle.primary, "Primary"))
        view.add_item(Button(ButtonStyle.secondary, "Secondary"))
        view.add_item(Button(ButtonStyle.success, "Success"))
        view.add_item(Button(ButtonStyle.danger, "Danger"))
        view.add_item(Button(ButtonStyle.link, "Link", url="https://example.com"))

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="dropdown")
    async def dropdown(self, interaction: discord.Interaction):
        options = [
            SelectOption(label="Price 1", value="100"),
            SelectOption(label="Price 2", value="200"),
            SelectOption(label="Price 3", value="300"),
        ]
        select = Select(placeholder="Choose a price", options=options)
        components = [[select]]
        await self.send_embed_with_data(interaction, "Data with Dropdown", "https://via.placeholder.com/150", components)

    @app_commands.command(name="mixed")
    async def mixed(self, interaction: discord.Interaction):
        options = [
            SelectOption(label="Price 1", value="100"),
            SelectOption(label="Price 2", value="200"),
            SelectOption(label="Price 3", value="300"),
        ]
        select = Select(placeholder="Choose a price", options=options)
        components = [
            [
                Button(label="Primary", style=ButtonStyle.primary),
                Button(label="Secondary", style=ButtonStyle.secondary),
            ],
            [select],
        ]
        await self.send_embed_with_data(interaction, "Data with Mixed UI", "https://via.placeholder.com/150", components)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if "component_type" not in interaction.data:
            return

        component_type = interaction.data["component_type"]

        if component_type == discord.ComponentType.button:
            await interaction.respond(content=f"You clicked the {interaction.component.label} button.", ephemeral=True)
        elif component_type == discord.ComponentType.select:
            selected_option = interaction.component.get_selected_options()[0]
            await interaction.respond(content=f"You selected price {selected_option.label} with value ${selected_option.value}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(DataDisplay(bot))
