import logging
import os

import aiohttp
import discord
from discord.ext import commands
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from redis import Redis

log = logging.getLogger(__name__)

class SkinPilot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents(
                guilds=True,
                members=True,
                bans=False,
                emojis=True,
                voice_states=True,
                messages=True,
                reactions=True,
                message_content=True,
            ),
            allowed_mentions=discord.AllowedMentions(roles=False, everyone=False, users=True),
        )

        self.engine = create_engine('postgresql://skinpilot:'+os.getenv("POSTGRES_PASSWORD")+'@db:5432/skinpilot_db')
        self.SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=self.engine))

        self.redis_conn = Redis(
            host="localhost",
            port=6379,
            db=0
        )

        self.initial_extensions = [
            "cogs.simple",
            "cogs.admin",
            "cogs.dice",
            "cogs.pricecheck",
        ]

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        for ext in self.initial_extensions:
            log.info(f"loading {ext}")
            self.load_extension(ext)  # load_extension is not an asynchronous method.

    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.uptime = discord.utils.utcnow()

        log.info(f"Ready: {self.user} (ID: {self.user.id})")

        # Call the setup_hook when the bot is ready
        await self.setup_hook()

    async def close(self):
        # When the bot is shutting down, close your database connections
        self.SessionLocal.remove()
        self.redis_conn.close()

        await super().close()


if __name__ == "__main__":
    bot = SkinPilot()
    bot.run(os.getenv("DISCORD_TOKEN"), root_logger=True)
