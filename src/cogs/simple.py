import discord
from discord import ui, app_commands
from discord.ext import commands

class TextInputModal(discord.ui.Modal, title="Text Input"):
    text_input = discord.ui.TextInput(label="Your input", placeholder="Enter your text here")

    async def on_submit(self, interaction: discord.Interaction):
        # Do something with the text input
        await interaction.response.send_message(f"You entered: {self.text_input.value}", ephemeral=True)


class DropdownWithTextInput(discord.ui.Select):
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "text_input_option":
            await interaction.response.send_modal(TextInputModal())
        else:
            await interaction.response.send_message(f"Selected option: {self.values[0]}", ephemeral=True)


def create_action_row():
    dropdown = DropdownWithTextInput(
        row=0,
        placeholder="Select an option",
        options=[
            discord.SelectOption(label="Option 1", value="1"),
            discord.SelectOption(label="Option 2", value="2"),
            discord.SelectOption(label="Text Input Option", value="text_input_option"),
        ],
    )

    view = discord.ui.View()
    view.add_item(dropdown)
    return view


class SimpleDropdownCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="simple", description="Displays an embed with an action row containing a dropdown")
    async def simple(self, interaction: discord.Interaction):
        await interaction.response.defer()

        action_row_view = create_action_row()

        embed = discord.Embed(title="Example Embed", description="This is a simple example with a dropdown.")
        await interaction.followup.send(embed=embed, view=action_row_view)

async def setup(bot):
    await bot.add_cog(SimpleDropdownCog(bot))