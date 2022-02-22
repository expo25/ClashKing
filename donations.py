import coc
import discord
import discord_slash
from HelperMethods.clashClient import client, coc_client, getPlayer

from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle

usafam = client.usafam
server = usafam.server
clans = usafam.clans
donations = usafam.donations

from discord.ext import commands

class WarEvents(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        coc_client.add_events(self.dona)
        coc_client.add_events(self.new_season)

    @commands.command(name="don")
    async def dono(self, ctx, *, aliases=None):
        tags = []
        if aliases is None:
            tracked = clans.find({"server": ctx.guild.id})
            limit = await clans.count_documents(filter={"server": ctx.guild.id})
            if limit == 0:
                return await ctx.send("This server has no linked clans.")
            for tClan in await tracked.to_list(length=limit):
                tag = tClan.get("tag")
                tags.append(tag)
        else:
            aliases = aliases.split(" ")
            if len(aliases) > 5:
                return await ctx.send(
                    f"Command only supports up to 5 clans.")
            for alias in aliases:
                results = await clans.find_one({"$and": [
                    {"alias": alias},
                    {"server": ctx.guild.id}
                ]})
                if results is None:
                    return await ctx.send(
                        f"Invalid alias {alias} found.\n**Note:** This command only supports single word aliases when given multiple.")
                tag = results.get("tag")
                tags.append(tag)

        rankings = []
        async for clan in coc_client.get_clans(tags):
            for member in clan.members:
                don = 0
                results = await donations.find_one({"tag": member.tag})
                if results is not None:
                    don = results.get("donations")
                else:
                    don = member.donations
                    await donations.insert_one({
                        "tag": member.tag,
                        "donations": don
                    })

                r = []
                r.append(member.name)
                r.append(don)
                r.append(clan.name)
                rankings.append(r)

        ranking = sorted(rankings, key=lambda l: l[1], reverse=True)
        ranking = ranking[0:50]

        text = ""
        x = 0
        for rr in ranking:
            place = str(x + 1) + "."
            place = place.ljust(3)
            do = "{:,}".format(rr[1])
            text += f"\u200e`{place}` \u200e<:troop:861797310224400434> \u200e{do} - \u200e{rr[0]} | \u200e{rr[2]}\n"
            x += 1

        embed = discord.Embed(title=f"**Top 50 Donators**",
                              description=text)
        embed.set_thumbnail(url=ctx.guild.icon_url_as())
        await ctx.send(embed=embed)


    @coc.ClientEvents.new_season_start()
    async def new_season(self):
        tracked = donations.find()
        limit = await donations.count_documents(filter={})
        for document in await tracked.to_list(length=limit):
            tag = document.get("tag")
            await donations.update_one({'tag': f"{tag}"},
                                           {'$set': {"donations": 0}})

    @coc.ClanEvents.member_donations()
    async def dona(self, old_member : coc.ClanMember, new_member : coc.ClanMember):
        donated = new_member.donations - old_member.donations
        tag = new_member.tag
        results = await donations.find_one({"tag": tag})
        if results is None:
            await donations.insert_one({
                "tag": tag,
                "donations": donated
            })
        else:
            await donations.update_one({"tag": tag}, {'$inc': {
                "donations": donated
            }})


def setup(bot: commands.Bot):
    bot.add_cog(WarEvents(bot))