import io
from datetime import datetime

import discord
from discord.ext import commands
import aiohttp

from Music import Music
from Roles import Roles

description = '''Role management bot'''
bot = commands.Bot(command_prefix='?', case_insensitive=True, description=description)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.event
async def on_message_edit(before, after):
    # Ignore pins and embeds
    if before.content == after.content:
        return

    channel = discord.utils.get(after.guild.channels, name="logs")

    embed = discord.Embed(title="Message Edited",
                          color=discord.Color.blurple(),
                          timestamp=datetime.now())\
        .set_author(name=after.author, icon_url=after.author.avatar_url)\
        .add_field(name="Before", value=before.content)\
        .add_field(name="After", value=after.content)\
        .add_field(name="Channel", value=after.channel.mention)

    await channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    channel = discord.utils.get(message.guild.channels, name="logs")

    if message.embeds and message.author.bot:
        return

    if message.attachments:
        for attached_content in message.attachments:
            if attached_content.proxy_url: # Easy way of detecting whether it's an image?
                embed = discord.Embed(title="Message Deleted",
                                      color=discord.Color.red(),
                                      timestamp=datetime.now()) \
                    .set_author(name=message.author, icon_url=message.author.avatar_url) \
                    .add_field(name="Message", value="This image was deleted.") \
                    .add_field(name="Channel", value=message.channel.mention)

                async with aiohttp.ClientSession() as session:
                    async with session.get(attached_content.proxy_url) as resp:
                        data = await resp.read()
                        image = io.BytesIO(data)
                        file  = discord.File(image, filename=attached_content.filename)

                        await channel.send(embed=embed, file=file)

    else:
        embed = discord.Embed(title="Message Deleted",
                              color=discord.Color.red(),
                              timestamp=datetime.now()) \
            .set_author(name=message.author, icon_url=message.author.avatar_url) \
            .add_field(name="Message", value=message.content) \
            .add_field(name="Channel", value=message.channel.mention)

        await channel.send(embed=embed)

@bot.command()
async def joined(ctx, member: discord.Member):
    """Says when a member joined."""
    await ctx.send('{0.name} joined at {0.joined_at}.'.format(member))

bot.add_cog(Music(bot))
bot.add_cog(Roles(bot))
bot.run('BOT_TOKEN')
