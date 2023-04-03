import random

import discord
from discord.ext import commands


class DiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="roll", description="Rolls 2 dice")
    async def roll(self, interaction):
        dice_1 = random.randint(1, 6)
        dice_2 = random.randint(1, 6)
        total = dice_1 + dice_2

        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"You rolled a {dice_1} and a {dice_2}. Total: {total}",
            color=discord.Color.blue(),
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(DiceCog(bot))
