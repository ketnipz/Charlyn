import random, string
import discord
from discord.ext import commands
from tinydb import TinyDB, Query

class Roles:
    def __init__(self, bot):
        self.bot = bot
        self.db = TinyDB('charlyn.json')

    @commands.group(aliases=["role"], case_insensitive=True)
    async def roles(self, ctx):
        """Role management, boi."""
        pass

    @roles.command(name='remove')
    @commands.has_permissions(administrator=True)
    async def _remove(self, ctx, reference_id: str):
        """Remove a role from the list of self-assignable roles."""
        Role = Query()

        role_result = self.db.search(Role.id == reference_id)

        if role_result:
            self.db.remove(Role.id == reference_id)
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
    async def _announce(self, ctx, channel: discord.TextChannel, title: str, body: str):
        embed = discord.Embed(title=title,
                              description=body,
                              color=discord.Color.teal())
        await channel.send(embed=embed)

    @roles.command(name='create')
    @commands.has_permissions(administrator=True)
    async def _create(self, ctx, channel: str, message_id: int, emoji: str, role_name: str):
        """Bind a role to a message and emoji."""
        bind_channel = discord.utils.get(ctx.message.guild.channels, mention=channel)

        if bind_channel is None:
            await ctx.send("That channel doesn't exist.", delete_after=5.0)
            return

        try:
            message = await bind_channel.get_message(message_id)

            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if role is None:
                await ctx.send("Role does not exist.", delete_after=5.0)
                return

            referenceId = str().join(random.choices(string.ascii_letters + string.digits, k=9))

            self.db.insert({"id": referenceId, "name": role_name, "message": message_id, "emoji": emoji})

            embed = discord.Embed(title="Role registered :tada:",
                                  description="Role **{}** has been registered by {}.".format(role, ctx.author.mention),
                                  color=discord.Color.teal()) \
            .add_field(name=":id: Reference ID", value=referenceId, inline=False) \
            .add_field(name=":tv: Channel", value=channel, inline=False) \
            .add_field(name=":speech_balloon: Message", value=message_id, inline=False) \
            .add_field(name=":arrow_down: Emoji", value=emoji, inline=False) \
            .add_field(name=":trident: Role", value=role_name, inline=False)

            await ctx.send(embed=embed)
            await message.add_reaction(emoji)

            await ctx.message.delete()

        except discord.errors.NotFound as notFoundError:
            await ctx.send(f":japanese_goblin: **Uh oh:** {notFoundError.text}. "
                           f"Please make sure you've specified the message's correct channel name and id.",
                           delete_after=15.0)

    async def on_guild_role_update(self, before, after):
        Role = Query()
        if self.db.search(Role.name == before.name):
            if before.name != after.name:
                self.db.update({'name': after.name}, Role.name == before.name)
                print(f'{before} has been renamed to {after} internally')


    async def on_guild_role_delete(self, role):
        Role = Query()
        if self.db.search(Role.name == role.name):
            self.db.remove(Role.name == role.name)
            print(f'{role} has been removed internally')

    async def on_raw_reaction_add(self, payload):
        Role = Query()
        message_exists = self.db.search(Role.message == payload.message_id)
        result = self.db.search((Role.emoji == str(payload.emoji)) & (Role.message == payload.message_id))

        if message_exists and not result:
            message = await self.bot.get_channel(payload.channel_id).get_message(payload.message_id)
            return await message.remove_reaction(payload.emoji, self.bot.get_user(payload.user_id))

        if result:
            guild = self.bot.get_guild(payload.guild_id)
            discord_role = discord.utils.get(guild.roles, name=result[0]["name"])
            member = guild.get_member(payload.user_id)

            if not member.bot:
                await member.add_roles(discord_role)


    async def on_raw_reaction_remove(self, payload):
        Role = Query()
        result = self.db.search((Role.emoji == str(payload.emoji)) & (Role.message == payload.message_id))

        if result:
            guild = self.bot.get_guild(payload.guild_id)
            discord_role = discord.utils.get(guild.roles, name=result[0]["name"])
            member = guild.get_member(payload.user_id)

            await member.remove_roles(discord_role)