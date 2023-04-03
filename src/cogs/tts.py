import logging
import os

import discord
from discord.ext import commands
from elevenlabslib import ElevenLabsUser

log = logging.getLogger(__name__)


class TTSCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user = ElevenLabsUser(os.getenv("elevenlabs_token"))
        self.voice = self.user.get_voices_by_name("testing")[0]

    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

    @commands.Cog.listener("on_message")
    async def tts(self, message):
        if message.channel.id != 1081842185135198208:
            return

        ctx = await self.bot.get_context(message)
        await self.ensure_voice(ctx)

        if message.content.lower() != "replay":
            tts_audio = self.voice.generate_audio_bytes(message.content)
            with open("ElevenLabs_tts.wav", mode="wb") as f:
                f.write(tts_audio)

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio("ElevenLabs_tts.wav"))
        ctx.voice_client.play(source)


async def setup(bot):
    await bot.add_cog(TTSCog(bot))
