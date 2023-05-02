import logging
import os

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

log = logging.getLogger(__name__)


def configure():
    load_dotenv()


class MyBot(commands.Bot):
    def __init__(self):
        allowed_mentions = discord.AllowedMentions(roles=False, everyone=False, users=True)
        intents = discord.Intents(
            guilds=True,
            members=True,
            bans=False,
            emojis=True,
            voice_states=True,
            messages=True,
            reactions=True,
            message_content=True,
        )
        super().__init__(command_prefix="!", intents=intents, allowed_mentions=allowed_mentions)
        self.initial_extensions = [
            # 'cogs.csgo',
            # "cogs.csgo_embed",
            "cogs.admin",
            "cogs.dice",
            "cogs.display_testing",
            "cogs.pricecheck",
        ]

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        for ext in self.initial_extensions:
            log.info(f"loading {ext}")
            await self.load_extension(ext)

    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.uptime = discord.utils.utcnow()

        log.info(f"Ready: {self.user} (ID: {self.user.id})")


if __name__ == "__main__":
    configure()
    bot = MyBot()
    bot.run(os.getenv("discord_token"), root_logger=True)
