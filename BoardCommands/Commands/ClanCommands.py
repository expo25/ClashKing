import coc
import disnake
import calendar
import pytz

from utils.ClanCapital import gen_raid_weekend_datestrings, get_raidlog_entry
from CustomClasses.CustomBot import CustomClient
from disnake.ext import commands
from typing import List
from ImageGen import ClanCapitalResult as capital_gen
from utils.constants import item_to_name, TOWNHALL_LEVELS, BOARD_TYPES
from utils.components import clan_board_components
from CustomClasses.CustomPlayer import MyCustomPlayer
from BoardCommands.Utils import Clan as clan_embeds
from BoardCommands.Utils import Shared as shared_embeds


class ClanCommands(commands.Cog, name="Clan Commands"):

    def __init__(self, bot: CustomClient):
        self.bot = bot

    async def clan_converter(self, clan: str):
        clan = await self.bot.getClan(clan_tag=clan, raise_exceptions=True)
        if clan is None:
            return coc.errors.NotFound
        if clan.member_count == 0:
            raise coc.errors.NotFound
        return clan

    async def season_convertor(self, season: str):
        if season is not None:
            month = list(calendar.month_name).index(season.split(" ")[0])
            year = season.split(" ")[1]
            end_date = coc.utils.get_season_end(month=int(month - 1), year=int(year))
            month = end_date.month
            if month <= 9:
                month = f"0{month}"
            season_date = f"{end_date.year}-{month}"
        else:
            season_date = self.bot.gen_season_date()
        return season_date


    @commands.slash_command(name="clan")
    async def clan(self, ctx: disnake.ApplicationCommandInteraction):
        result = await self.bot.user_settings.find_one({"discord_user" : ctx.author.id})
        ephemeral = False
        if result is not None:
            ephemeral = result.get("private_mode", False)
        if "board" in ctx.filled_options.keys():
            ephemeral = True
        await ctx.response.defer(ephemeral=ephemeral)


    @clan.sub_command(name="search", description="Various clan boards - donation, links, etc")
    async def clan_boards(self, ctx: disnake.ApplicationCommandInteraction, clan: coc.Clan = commands.Param(converter=clan_converter),
                          type: str= commands.Param(choices=BOARD_TYPES),
                          season: str= commands.Param(default=None, converter=season_convertor)):
        db_clan = await self.bot.get_stat_clan(clan_tag=clan.tag, clan=clan)
        type = type.replace(" ", "-").lower()
        embeds = await clan_embeds.type_to_board(bot=self.bot, db_clan=db_clan, type=type, season=season, guild=ctx.guild)

        components = clan_board_components(bot=self.bot, season=season, clan_tag=clan.tag, type=type)
        await ctx.edit_original_message(embeds=embeds, components=components)


    @clan.sub_command(name="progress", description="Progress by clan ")
    async def progress(self, ctx: disnake.ApplicationCommandInteraction,
                       clan: coc.Clan = commands.Param(converter=clan_converter),
                       type=commands.Param(choices=["Heroes & Pets", "Troops, Spells, & Sieges", "Loot"]),
                       season: str = commands.Param(default=None, convert_defaults=True, converter=season_convertor),
                       limit: int = commands.Param(default=50, min_value=1, max_value=50)):
        """
            Parameters
            ----------
            clan: Use clan tag or select an option from the autocomplete
            type: progress type
            season: clash season to view data for
            limit: change amount of results shown
        """
        buttons = []
        if type == "Heroes & Pets":
            embed = await shared_embeds.hero_progress(bot=self.bot, player_tags=[member.tag for member in clan.members], season=season,
                                                      footer_icon=clan.badge.url, title_name=f"{clan.name} {type} Progress", limit=limit)
            buttons = disnake.ui.ActionRow()
            buttons.append_item(disnake.ui.Button(
                label="", emoji=self.bot.emoji.magnify_glass.partial_emoji,
                style=disnake.ButtonStyle.grey, custom_id=f"clanmoreprogress_{clan.tag}_{season}_heroes"))
        elif type == "Troops, Spells, & Sieges":
            embed = await shared_embeds.troops_spell_siege_progress(bot=self.bot, player_tags=[member.tag for member in clan.members],
                                                      season=season,
                                                      footer_icon=clan.badge.url,
                                                      title_name=f"{clan.name} {type} Progress", limit=limit)
            buttons = disnake.ui.ActionRow()
            buttons.append_item(disnake.ui.Button(
                label="", emoji=self.bot.emoji.magnify_glass.partial_emoji,
                style=disnake.ButtonStyle.grey, custom_id=f"clanmoreprogress_{clan.tag}_{season}_troopsspells"))
        elif type == "Home Trophies":
            embed = await shared_embeds.trophies_progress(bot=self.bot,
                                                                    player_tags=[member.tag for member in clan.members],
                                                                    season=season,
                                                                    footer_icon=clan.badge.url,
                                                                    title_name=f"{clan.name} {type} Progress",
                                                                    limit=limit, type="home")
        elif type == "Builder Trophies":
            embed = await shared_embeds.trophies_progress(bot=self.bot,
                                                                    player_tags=[member.tag for member in clan.members],
                                                                    season=season,
                                                                    footer_icon=clan.badge.url,
                                                                    title_name=f"{clan.name} {type} Progress",
                                                                    limit=limit, type="builder")
        elif type == "Loot":
            embed = await shared_embeds.loot_progress(bot=self.bot,
                                                          player_tags=[member.tag for member in clan.members],
                                                          season=season,
                                                          footer_icon=clan.badge.url,
                                                          title_name=f"{clan.name} {type} Progress",
                                                          limit=limit)

        await ctx.edit_original_message(embed=embed, components=[buttons] if buttons else [])


    @clan.sub_command(name="sorted", description="List of clan members, sorted by any attribute")
    async def sorted(self, ctx: disnake.ApplicationCommandInteraction, clan: coc.Clan = commands.Param(converter=clan_converter),
                     sort_by: str = commands.Param(choices=sorted(item_to_name.keys())),
                     limit: int = commands.Param(default=50, min_value=1, max_value=50)):
        """
            Parameters
            ----------
            clan: Use clan tag or select an option from the autocomplete
            sort_by: Sort by any attribute
            limit: change amount of results shown
        """

        embed = await shared_embeds.player_sort(bot=self.bot, player_tags=[member.tag for member in clan.members], sort_by=sort_by,
                                                footer_icon=clan.badge.url, title_name=f"{clan.name} sorted by {sort_by}", limit=limit)

        buttons = disnake.ui.ActionRow()
        buttons.append_item(disnake.ui.Button(
            label="", emoji=self.bot.emoji.refresh.partial_emoji,
            style=disnake.ButtonStyle.grey,
            custom_id=f"clansort_{clan.tag}_{limit}_{sort_by}"))

        await ctx.edit_original_message(embed=embed, components=[buttons])


    @clan.sub_command(name="compo", description="Composition of a clan. (with a twist?)")
    async def compo(self, ctx: disnake.ApplicationCommandInteraction,
                         clan: coc.Clan = commands.Param(converter=clan_converter),
                        type: str = commands.Param(default="Totals", choices=["Totals", "Hitrate"])):
        """
            Parameters
            ----------
            clan: Use clan tag or select an option from the autocomplete
            type: type of compo calculation
        """
        if type == "Totals":
            embed = await shared_embeds.th_composition(bot=self.bot, player_tags=[member.tag for member in clan.members],
                                                       title=f"{clan.name} Townhall Composition", thumbnail=clan.badge.url)
            custom_id = f"clancompo_{clan.tag}"
        elif type == "Hitrate":
            embed = await shared_embeds.th_hitrate(bot=self.bot,
                                                       player_tags=[member.tag for member in clan.members],
                                                       title=f"{clan.name} TH Hitrate Compo",
                                                       thumbnail=clan.badge.url)
            custom_id = f"clanhrcompo_{clan.tag}"

        buttons = disnake.ui.ActionRow()
        buttons.append_item(
            disnake.ui.Button(
                label="", emoji=self.bot.emoji.refresh.partial_emoji,
                style=disnake.ButtonStyle.grey,
                custom_id=custom_id))

        await ctx.edit_original_message(embed=embed, components=buttons)


    @clan.sub_command(name="board", description="Image Board")
    async def board(self, ctx: disnake.ApplicationCommandInteraction, clan: coc.Clan= commands.Param(converter=clan_converter),
                    board: str = commands.Param(choices=["Activity", "Legends", "Trophies"])):

        players: List[MyCustomPlayer] = await self.bot.get_players(tags=[member.tag for member in clan.members], custom=True)

        if board == "Activity":
            players.sort(key=lambda x: x.donos().donated, reverse=False)
            file = await shared_embeds.image_board(bot=self.bot, players=players, logo_url=clan.badge.url, title=f'{clan.name} Activity/Donation Board',
                                                            season=self.bot.gen_season_date(), type="activities")
            board_type = "clanboardact"
        elif board == "Legends":
            players = [player for player in players if player.is_legends()]
            players.sort(key=lambda x: x.trophies, reverse=False)
            file = await shared_embeds.image_board(bot=self.bot, players=players, logo_url=clan.badge.url, title=f'{clan.name} Legend Board', type="legend")
            board_type = "clanboardlegend"
        elif board == "Trophies":
            players.sort(key=lambda x: x.trophies, reverse=False)
            file = await shared_embeds.image_board(bot=self.bot, players=players, logo_url=clan.badge.url, title=f'{clan.name} Trophy Board', type="trophies")
            board_type = "clanboardtrophies"


        await ctx.edit_original_message(content="Image Board Created!")

        buttons = disnake.ui.ActionRow()
        buttons.append_item(disnake.ui.Button(
            label="", emoji=self.bot.emoji.refresh.partial_emoji,
            style=disnake.ButtonStyle.grey, custom_id=f"{board_type}_{clan.tag}"))
        await ctx.channel.send(file=file, components=[buttons])



    @clan.sub_command(name="graphs")
    async def activity_graph(self, ctx: disnake.ApplicationCommandInteraction, clan: coc.Clan = commands.Param(converter=clan_converter),
                       type: str = commands.Param(choices=["Activity"]),
                       season: str = commands.Param(default=None, converter=season_convertor),
                       timezone: str = "UTC"):
        s = season if season is not None else self.bot.gen_season_date()
        if type == "Activity":
            players = await self.bot.get_players(tags=[member.tag for member in clan.members])
            file, buttons = await shared_embeds.activity_graph(bot=self.bot, players=players, season=season, title=f"{clan.name} Activity ({s}) | {timezone}",
                                                               granularity="day", time_zone=timezone, tier=f"clanactgraph_{clan.tag}")
            await ctx.send(file=file, components=[buttons])


    @clan.sub_command(name="capital", description="Clan capital info for a clan for a week")
    async def clan_capital(self, ctx: disnake.ApplicationCommandInteraction, clan: coc.Clan = commands.Param(converter=clan_converter), weekend: str = None):
        #3 types - overview, donations, & raids
        week = weekend
        if weekend is None:
            week = gen_raid_weekend_datestrings(number_of_weeks=1)[0]

        weekend_raid_entry = await get_raidlog_entry(clan=clan, weekend=week, bot=self.bot, limit=1)
        if weekend_raid_entry is None:
            embed = await clan_embeds.clan_raid_weekend_donation_stats(bot=self.bot, clan=clan, weekend=week)
        else:
            embed = await clan_embeds.clan_capital_overview(bot=self.bot, clan=clan, raid_log_entry=weekend_raid_entry)
            file = await capital_gen.generate_raid_result_image(raid_entry=weekend_raid_entry, clan=clan)
            embed.set_image(file=file)

        page_buttons = [
            disnake.ui.Button(label="", emoji=self.bot.emoji.menu.partial_emoji,
                              style=disnake.ButtonStyle.grey,
                              custom_id=f"capitaloverview_{clan.tag}_{weekend}"),
            disnake.ui.Button(label="Raids", emoji=self.bot.emoji.sword_clash.partial_emoji, style=disnake.ButtonStyle.grey,
                              custom_id=f"capitalraids_{clan.tag}_{weekend}"),
            disnake.ui.Button(label="Donos", emoji=self.bot.emoji.capital_gold.partial_emoji,
                              style=disnake.ButtonStyle.grey,
                              custom_id=f"capitaldonos_{clan.tag}_{weekend}")
        ]
        buttons = disnake.ui.ActionRow()
        for button in page_buttons:
            buttons.append_item(button)

        return await ctx.send(embed=embed, components=[buttons])


    #AUTOCOMPLETES
    @activity_graph.autocomplete("season")
    @progress.autocomplete("season")
    @clan_boards.autocomplete("season")
    async def season(self, ctx: disnake.ApplicationCommandInteraction, query: str):
        seasons = self.bot.gen_season_date(seasons_ago=12)[0:]
        return [season for season in seasons if query.lower() in season.lower()]

    @activity_graph.autocomplete("clan")
    @clan_capital.autocomplete("clan")
    @progress.autocomplete("clan")
    @sorted.autocomplete("clan")
    @compo.autocomplete("clan")
    @board.autocomplete("clan")
    @clan_boards.autocomplete("clan")
    async def autocomp_clan(self, ctx: disnake.ApplicationCommandInteraction, query: str):
        tracked = self.bot.clan_db.find({"server": ctx.guild.id}).sort("name", 1)
        limit = await self.bot.clan_db.count_documents(filter={"server": ctx.guild.id})
        clan_list = []
        for tClan in await tracked.to_list(length=limit):
            name = tClan.get("name")
            tag = tClan.get("tag")
            if query.lower() in name.lower():
                clan_list.append(f"{name} | {tag}")

        if clan_list == [] and len(query) >= 3:
            if coc.utils.is_valid_tag(query):
                clan = await self.bot.getClan(query)
            else:
                clan = None
            if clan is None:
                results = await self.bot.coc_client.search_clans(name=query, limit=5)
                for clan in results:
                    league = str(clan.war_league).replace("League ", "")
                    clan_list.append(
                        f"{clan.name} | {clan.member_count}/50 | LV{clan.level} | {league} | {clan.tag}")
            else:
                clan_list.append(f"{clan.name} | {clan.tag}")
                return clan_list
        return clan_list[0:25]

    @activity_graph.autocomplete("timezone")
    async def timezone_autocomplete(self, ctx: disnake.ApplicationCommandInteraction, query: str):
        all_tz = pytz.common_timezones
        return_list = []
        for tz in all_tz:
            if query.lower() in tz.lower():
                return_list.append(tz)
        return return_list[:25]

    @clan_capital.autocomplete("weekend")
    async def weekend(self, ctx: disnake.ApplicationCommandInteraction, query: str):
        weekends = gen_raid_weekend_datestrings(number_of_weeks=25)
        matches = []
        for weekend in weekends:
            if query.lower() in weekend.lower():
                matches.append(weekend)
        return matches

def setup(bot):
    bot.add_cog(ClanCommands(bot))

