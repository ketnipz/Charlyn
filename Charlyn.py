import random, string
from datetime import datetime
import discord
from discord.ext import commands
import aiohttp
import io

from tinydb import TinyDB, Query
#from Music import Music
#from Speech import Speech

db = TinyDB('charlyn.json')

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

    if message.attachments:
        for attached_content in message.attachments:
            if attached_content.proxy_url: # Easy way of detecting whether it's an image?
                embed = discord.Embed(title="Message Deleted",
                                      color=discord.Color.red(),
                                      timestamp=datetime.now()) \
                    .set_author(name=message.author, icon_url=message.author.avatar_url) \
                    .add_field(name="Message", value="This user deleted an image.") \
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

@bot.event
async def on_guild_role_update(before, after):
    Role = Query()
    if db.search(Role.name == before.name):
        if before.name != after.name:
            db.update({'name': after.name}, Role.name == before.name)
            print(f'{before} has been renamed to {after} internally')

@bot.event
async def on_guild_role_delete(role):
    Role = Query()
    if db.search(Role.name == role.name):
        db.remove(Role.name == role.name)
        print(f'{role} has been removed internally')

@bot.command()
async def joined(ctx, member: discord.Member):
    """Says when a member joined."""
    await ctx.send('{0.name} joined at {0.joined_at}.'.format(member))

@bot.group(aliases=["role"], case_insensitive=True)
async def roles(ctx):
    """Role management, boi."""
    pass

@roles.command(name='add')
@commands.has_permissions(administrator=True)
async def _add(ctx, role: str):
    """Add a role to the list of self-assignable roles."""
    async with ctx.message.channel.typing():
        if discord.utils.get(ctx.guild.roles, name=role) is not None:
            db.insert({"name": role})
            embed = discord.Embed(title="Role registered",
                                  description="Role **{}** has been registered by {}.".format(role, ctx.author.mention),
                                  color=discord.Color.teal())
            await ctx.send(embed=embed)
        else:
            await ctx.send("Invalid role specified.", delete_after=5.0)

@roles.command(name='remove')
@commands.has_permissions(administrator=True)
async def _remove(ctx, reference_id: str):
    """Remove a role from the list of self-assignable roles."""
    Role = Query()

    role_result = db.search(Role.id == reference_id)

    if role_result:
        db.remove(Role.id == reference_id)
        embed = discord.Embed(title="Role removed",
                              description="Role **{}** has been removed by {}."
                              .format(role_result[0]["name"], ctx.author.mention),
                              color=discord.Color.teal()) \
        .add_field(name=":speech_balloon: Message", value=role_result[0]["message"], inline=False) \
        .add_field(name=":arrow_down: Emoji", value=role_result[0]["emoji"], inline=False) \
        .add_field(name=":trident: Role", value=role_result[0]["name"], inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("This reference id is invalid.", delete_after=10.0)

@roles.command(name='announce')
@commands.has_permissions(administrator=True)
async def _announce(ctx, channel: discord.TextChannel, title: str, body: str):
    embed = discord.Embed(title=title,
                          description=body,
                          color=discord.Color.teal())
    await channel.send(embed=embed)

@roles.command(name='create')
@commands.has_permissions(administrator=True)
async def _create(ctx, channel: str, message_id: int, emoji: str, role_name: str):
    """Bind a role to a message and emoji."""
    bind_channel = discord.utils.get(ctx.message.guild.channels, mention=channel)

    if bind_channel is None:
        await ctx.send("That channel doesn't exist.", delete_after=5.0)
        return

    try:
        await bind_channel.get_message(message_id)

        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role is None:
            await ctx.send("Role does not exist.", delete_after=5.0)
            return

        referenceId = str().join(random.choices(string.ascii_letters + string.digits, k=9))

        db.insert({"id": referenceId, "name": role_name, "message": message_id, "emoji": emoji})

        embed = discord.Embed(title="Role registered :tada:",
                              description="Role **{}** has been registered by {}.".format(role, ctx.author.mention),
                              color=discord.Color.teal()) \
        .add_field(name=":id: Reference ID", value=referenceId, inline=False) \
        .add_field(name=":tv: Channel", value=channel, inline=False) \
        .add_field(name=":speech_balloon: Message", value=message_id, inline=False) \
        .add_field(name=":arrow_down: Emoji", value=emoji, inline=False) \
        .add_field(name=":trident: Role", value=role_name, inline=False)

        await ctx.send(embed=embed)

        await ctx.message.delete()

    except discord.errors.NotFound as notFoundError:
        await ctx.send(f":japanese_goblin: **Uh oh:** {notFoundError.text}. "
                       f"Please make sure you've specified the message's correct channel name and id.",
                       delete_after=15.0)

@bot.event
async def on_raw_reaction_add(payload):
    Role = Query()
    result = db.search((Role.emoji == str(payload.emoji)) & (Role.message == payload.message_id))

    if result:
        guild = bot.get_guild(payload.guild_id)
        discordRole = discord.utils.get(guild.roles, name=result[0]["name"])
        member = guild.get_member(payload.user_id)
        await guild.get_member(payload.user_id).add_roles(discordRole)
        await guild.get_channel(payload.channel_id).send(f"{member.mention} I have assigned your role.", delete_after=5.0)

@bot.event
async def on_raw_reaction_remove(payload):
    Role = Query()
    result = db.search((Role.emoji == str(payload.emoji)) & (Role.message == payload.message_id))

    if result:
        guild = bot.get_guild(payload.guild_id)
        discordRole = discord.utils.get(guild.roles, name=result[0]["name"])
        member = guild.get_member(payload.user_id)
        await member.remove_roles(discordRole)
        await guild.get_channel(payload.channel_id).send(f"{member.mention} I have removed your role.", delete_after=5.0)

#bot.add_cog(Music(bot))
#bot.add_cog(Speech(bot))
bot.run('BOT_TOKEN')
