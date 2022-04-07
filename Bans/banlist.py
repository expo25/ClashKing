
from disnake.ext import commands
from utils.clash import getPlayer, client, pingToChannel, player_handle, coc_client
import disnake
from utils.components import create_components
from datetime import datetime

from Dictionaries.emojiDictionary import emojiDictionary

usafam = client.usafam
banlist = usafam.banlist
server = usafam.server


class banlists(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot



    @commands.slash_command(name="ban", description="stuff")
    async def ban(self, ctx):
        pass

    @ban.sub_command(name='list', description="This server's list of banned players")
    async def ban_list(self, ctx: disnake.ApplicationCommandInteraction):

        perms = ctx.author.guild_permissions.manage_guild
        if not perms:
            embed = disnake.Embed(description="Command requires you to have `Manage Server` permissions.",
                                  color=disnake.Color.red())
            return await ctx.send(embed=embed)

        await ctx.response.defer()

        embeds = await self.create_embeds(ctx)
        if embeds == []:
            embed = disnake.Embed(
                description="No banned players on this server.",
                color=disnake.Color.green())
            return await ctx.edit_original_message(embed=embed)


        current_page = 0
        await ctx.edit_original_message(embed=embeds[0], components=create_components(current_page, embeds, True))
        msg = await ctx.original_message()

        def check(res: disnake.MessageInteraction):
            return res.message.id == msg.id

        while True:
            try:
                res: disnake.MessageInteraction = await self.bot.wait_for("message_interaction", check=check,
                                                                          timeout=600)
            except:
                await msg.edit(components=[])
                break

            if res.data.custom_id == "Previous":
                current_page -= 1
                await res.response.edit_message(embed=embeds[current_page],
                               components=create_components(current_page, embeds, True))

            elif res.data.custom_id == "Next":
                current_page += 1
                await res.response.edit_message(embed=embeds[current_page],
                               components=create_components(current_page, embeds, True))

            elif res.data.custom_id == "Print":
                await msg.delete()
                for embed in embeds:
                    await ctx.channel.send(embed=embed)


    @ban.sub_command(name='add', description="Add player to server ban list")
    async def ban_add(self, ctx: disnake.ApplicationCommandInteraction, tag: str, reason :str= "None"):
        """
            Parameters
            ----------
            tag: player_tag to ban
            reason: reason for ban
        """

        perms = ctx.author.guild_permissions.manage_guild
        if not perms:
            embed = disnake.Embed(description="Command requires you to have `Manage Server` permissions.",
                                  color=disnake.Color.red())
            return await ctx.send(embed=embed)

        player = await getPlayer(tag)
        if player is None:
            return await player_handle(ctx, tag)


        results = await banlist.find_one({"$and": [
            {"VillageTag": player.tag},
            {"server": ctx.guild.id}
        ]})

        if results is not None and reason == "None":
            embed = disnake.Embed(description=f"{player.name} is already banned on this server.\nProvide `reason` to update ban notes.",
                                  color=disnake.Color.red())
            return await ctx.send(embed=embed)
        elif results is not None and reason != "None":
            await banlist.update_one({"$and": [
                {"VillageTag": player.tag},
                {"server": ctx.guild.id}
            ]}, {'$set': {"Notes": reason}})
            embed = disnake.Embed(
                description=f"[{player.name}]({player.share_link}) ban reason updated by {ctx.author.mention}.\n"
                            f"Notes: {reason}",
                color=disnake.Color.green())
            return await ctx.send(embed=embed)


        now = datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")

        await banlist.insert_one({
            "VillageTag": player.tag,
            "DateCreated": dt_string,
            "Notes": reason,
            "server": ctx.guild.id
        })
        embed2 = disnake.Embed(description=f"[{player.name}]({player.share_link}) added to the banlist by {ctx.author.mention}.\n"
                                          f"Notes: {reason}",
                               color=disnake.Color.green())
        await ctx.send(embed=embed2)

        results = await server.find_one({"server": ctx.guild.id})
        banChannel = results.get("banlist")
        channel = await pingToChannel(ctx,banChannel)

        if channel is not None:
            x = 0
            async for message in channel.history(limit=None):
                await message.delete()
                x += 1
                if x == 100:
                    break
            embeds = await self.create_embeds(ctx)
            for embed in embeds:
                await channel.send(embed=embed)
            await channel.send(embed=embed2)


    @ban.sub_command(name='remove', description="Remove player from server ban list")
    async def ban_remove(self, ctx: disnake.ApplicationCommandInteraction, tag: str):
        """
            Parameters
            ----------
            tag: player_tag to unban
        """

        perms = ctx.author.guild_permissions.manage_guild
        if not perms:
            embed = disnake.Embed(description="Command requires you to have `Manage Server` permissions.",
                                  color=disnake.Color.red())
            return await ctx.send(embed=embed)

        player = await getPlayer(tag)
        if player is None:
            return await player_handle(ctx, tag)

        results = await banlist.find_one({"$and": [
            {"VillageTag": player.tag},
            {"server": ctx.guild.id}
        ]})
        if results is None:
            embed = disnake.Embed(description=f"{player.name} is not banned on this server.",
                                  color=disnake.Color.red())
            return await ctx.send(embed=embed)

        await banlist.find_one_and_delete({"$and": [
            {"VillageTag": player.tag},
            {"server": ctx.guild.id}
        ]})

        embed2 = disnake.Embed(description=f"[{player.name}]({player.share_link}) removed from the banlist by {ctx.author.mention}.",
                              color=disnake.Color.green())
        await ctx.send(embed=embed2)

        results = await server.find_one({"server": ctx.guild.id})
        banChannel = results.get("banlist")
        channel = await pingToChannel(ctx, banChannel)
        if channel is not None:
            async for message in channel.history(limit=None):
                await message.delete()
            embeds = await self.create_embeds(ctx)
            for embed in embeds:
                await channel.send(embed=embed)
            await channel.send(embed=embed2)


    async def create_embeds(self, ctx):
        text = []
        hold = ""
        num = 0
        all = banlist.find({"server": ctx.guild.id}).sort("DateCreated", 1)
        limit = await banlist.count_documents(filter={"server": ctx.guild.id})
        if limit == 0:
            return []

        for ban in await all.to_list(length=limit):
            tag = ban.get("VillageTag")
            player = await getPlayer(tag)
            if player is None:
                continue
            name = player.name
            # name = name.replace('*', '')
            date = ban.get("DateCreated")
            date = date[0:10]
            notes = ban.get("Notes")
            if notes == "":
                notes = "No Notes"
            clan = ""
            try:
                clan = player.clan.name
                clan = f"{clan}, {str(player.role)}"
            except:
                clan = "No Clan"
            hold += f"{emojiDictionary(player.town_hall)}[{name}]({player.share_link}) | {player.tag}\n" \
                    f"{clan}\n" \
                    f"Added on: {date}\n" \
                    f"*{notes}*\n\n"
            num += 1
            if num == 10:
                text.append(hold)
                hold = ""
                num = 0

        if num != 0:
            text.append(hold)

        embeds = []
        for t in text:
            embed = disnake.Embed(title=f"{ctx.guild.name} Ban List",
                                  description=t,
                                  color=disnake.Color.green())
            if ctx.guild.icon is not None:
                embed.set_thumbnail(url=ctx.guild.icon.url)
            embeds.append(embed)

        return embeds


def setup(bot: commands.Bot):
    bot.add_cog(banlists(bot))