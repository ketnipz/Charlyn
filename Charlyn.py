import random
from datetime import datetime
import discord
from discord.ext import commands

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
    # print(

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

    embed = discord.Embed(title="Message Deleted",
                          color=discord.Color.red(),
                          timestamp=datetime.now())\
        .set_author(name=message.author, icon_url=message.author.avatar_url)\
        .add_field(name="Message", value=message.content)\
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
async def on_reaction_add(reaction, user):
    print(f'{user} reacted with {reaction.emoji}')

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
async def _remove(ctx, role: str):
    """Remove a role from the list of self-assignable roles."""
    async with ctx.message.channel.typing():
        Role = Query()

        if db.search(Role.name == role):
            db.remove(Role.name == role)
            embed = discord.Embed(title="Role removed",
                                  description="Role **{}** has been removed by {}.".format(role, ctx.author.mention),
                                  color=discord.Color.teal())
            await ctx.send(embed=embed)
        else:
            await ctx.send("This role is not in the list of self-assignable roles.", delete_after=5.0)

@roles.command(name='list')
async def _list(ctx):
    """List all of the available roles."""
    async with ctx.message.channel.typing():
        roleList = db.all()

        roleListMessage = \
            "List of assignable roles:\n```{0}```\n" \
            "You can use `{1}roles assign` to assign yourself an available role (e.g. `{1}roles assign {2}`)." \
            .format("\n".join(("{}. {}".format(roleIndex, roleName["name"])
                               for roleIndex, roleName in enumerate(roleList, 1))
        ), ctx.prefix, random.choice(roleList)["name"])

        await ctx.send(roleListMessage, delete_after=25.0)

@roles.command(name='assign')
async def _assign(ctx, role_name: str):
    """Assign yourself a role."""
    async with ctx.message.channel.typing():
        if role_name.isdigit():
            roleList = db.all()
            roleIndex = int(role_name)
            if not 0 < roleIndex <= len(roleList):
                await ctx.send("This role does not exist!", delete_after=5.0)
                return
            role_name = roleList[roleIndex - 1]["name"]

        Role = Query()
        discordRole = discord.utils.get(ctx.guild.roles, name=role_name)
        if discordRole is None:
            await ctx.send("This role does not exist!", delete_after=5.0)
        elif not db.search(Role.name == role_name):
            await ctx.send("This is not a self-assignable role.", delete_after=5.0)
        else:
            try:
                await ctx.author.add_roles(discordRole)
                await ctx.send("I have assigned your role.", delete_after=5.0)
            except discord.Forbidden:
                await ctx.send("I am not allowed to assign that role.", delete_after=5.0)

@roles.command(name='unassign')
async def _unassign(ctx, role_name: str):
    """Unassign a role."""
    async with ctx.message.channel.typing():
        Role = Query()
        discordRole = discord.utils.get(ctx.guild.roles, name=role_name)
        if discordRole is None:
            await ctx.send("This role does not exist!", delete_after=5.0)
        elif not db.search(Role.name == role_name):
            await ctx.send("This is not a self-assignable role.", delete_after=5.0)
        else:
            try:
                await ctx.author.remove_roles(discordRole)
                await ctx.send("I have removed your role.", delete_after=5.0)
            except discord.Forbidden:
                await ctx.send("I am not allowed to remove that role.", delete_after=5.0)

#bot.add_cog(Music(bot))
#bot.add_cog(Speech(bot))
bot.run('BOT_TOKEN')
