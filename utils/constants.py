import json

#EVAL CONSTANTS
DEFAULT_EVAL_ROLE_TYPES = ["family", "not_family", "clan", "leadership", "townhall", "builderhall", "category", "league", "builder_league", "achievement", "status", "nicknames"]
ROLE_TREATMENT_TYPES = ["Add", "Remove"]

BOARD_TYPES = ["Overview Board", "Simple Board", "Summary", "Donation", "Received", "Dono Ratio", "Discord Links", "War Preference", "Super Troops", "Clan Games", "Activity", "Last Online", "War Log", "CWL History"]
TOWNHALL_LEVELS = [x for x in range(1, 16)]
MAX_NUM_SUPERS = 2
SHORT_PLAYER_LINK = "https://api.clashking.xyz/p/"
SHORT_CLAN_LINK = "https://api.clashking.xyz/c/"

item_to_name = {"Player Tag" : "tag", "Role" : "role",
                "Versus Trophies" : "versus-trophies", "Trophies" : "trophies",
                "Clan Capital Contributions" : "clan-capital-contributions", "Clan Capital Raided" : "ach-Aggressive Capitalism",
                "XP Level" : "exp-level", "Combined Heroes" : "heroes", "Obstacles Removed" : "ach-Nice and Tidy", "War Stars" : "war-stars",
                "DE Looted" : "ach-Heroic Heist", "CWL Stars" : "ach-War League Legend", "Attacks Won (all time)" : "ach-Conqueror",
                "Attacks Won (season)" : "attack-wins", "Defenses Won (season)" : "defense-wins", "Defenses Won (all time)" : "ach-Unbreakable", "Total Donated" : "ach-Friend in Need",
                "Versus Trophy Record" : "ach-Champion Builder", "Trophy Record" : "ach-Sweet Victory!",
                "Clan Games Points" : "ach-Games Champion", "Versus Battles Won" : "versus-attack-wins", "Best Season Rank" : "legendStatistics.bestSeason.rank", "Townhall Level" : "townHallLevel"}

HOME_VILLAGE_HEROES = ["Barbarian King", "Archer Queen", "Royal Champion", "Grand Warden"]

locations = ["global", 32000007, 32000008, 32000009, 32000010, 32000011, 32000012, 32000013, 32000014, 32000015, 32000016,
             32000017,
             32000018, 32000019, 32000020, 32000021, 32000022, 32000023, 32000024, 32000025, 32000026, 32000027,
             32000028,
             32000029, 32000030, 32000031, 32000032, 32000033, 32000034, 32000035, 32000036, 32000037, 32000038,
             32000039,
             32000040, 32000041, 32000042, 32000043, 32000044, 32000045, 32000046, 32000047, 32000048, 32000049,
             32000050,
             32000051, 32000052, 32000053, 32000054, 32000055, 32000056, 32000057, 32000058, 32000059, 32000060,
             32000061,
             32000062, 32000063, 32000064, 32000065, 32000066, 32000067, 32000068, 32000069, 32000070, 32000071,
             32000072,
             32000073, 32000074, 32000075, 32000076, 32000077, 32000078, 32000079, 32000080, 32000081, 32000082,
             32000083,
             32000084, 32000085, 32000086, 32000087, 32000088, 32000089, 32000090, 32000091, 32000092, 32000093,
             32000094,
             32000095, 32000096, 32000097, 32000098, 32000099, 32000100, 32000101, 32000102, 32000103, 32000104,
             32000105,
             32000106, 32000107, 32000108, 32000109, 32000110, 32000111, 32000112, 32000113, 32000114, 32000115,
             32000116,
             32000117, 32000118, 32000119, 32000120, 32000121, 32000122, 32000123, 32000124, 32000125, 32000126,
             32000127,
             32000128, 32000129, 32000130, 32000131, 32000132, 32000133, 32000134, 32000135, 32000136, 32000137,
             32000138,
             32000139, 32000140, 32000141, 32000142, 32000143, 32000144, 32000145, 32000146, 32000147, 32000148,
             32000149,
             32000150, 32000151, 32000152, 32000153, 32000154, 32000155, 32000156, 32000157, 32000158, 32000159,
             32000160,
             32000161, 32000162, 32000163, 32000164, 32000165, 32000166, 32000167, 32000168, 32000169, 32000170,
             32000171,
             32000172, 32000173, 32000174, 32000175, 32000176, 32000177, 32000178, 32000179, 32000180, 32000181,
             32000182,
             32000183, 32000184, 32000185, 32000186, 32000187, 32000188, 32000189, 32000190, 32000191, 32000192,
             32000193,
             32000194, 32000195, 32000196, 32000197, 32000198, 32000199, 32000200, 32000201, 32000202, 32000203,
             32000204,
             32000205, 32000206, 32000207, 32000208, 32000209, 32000210, 32000211, 32000212, 32000213, 32000214,
             32000215,
             32000216, 32000217, 32000218, 32000219, 32000220, 32000221, 32000222, 32000223, 32000224, 32000225,
             32000226,
             32000227, 32000228, 32000229, 32000230, 32000231, 32000232, 32000233, 32000234, 32000235, 32000236,
             32000237,
             32000238, 32000239, 32000240, 32000241, 32000242, 32000243, 32000244, 32000245, 32000246, 32000247,
             32000248,
             32000249, 32000250, 32000251, 32000252, 32000253, 32000254, 32000255, 32000256, 32000257, 32000258,
             32000259, 32000260]

BADGE_GUILDS = [1029631304817451078, 1029631182196977766, 1029631107240562689, 1029631144641183774, 1029629452403097651,
                             1029629694854828082, 1029629763087777862, 1029629811221610516, 1029629853017841754, 1029629905903833139,
                             1029629953907634286, 1029629992830783549, 1029630376911581255, 1029630455202455563, 1029630702125318144,
                             1029630796966932520, 1029630873588469760, 1029630918106824754, 1029630974025277470, 1029631012084396102]

LEVELS_AND_XP = {
    '0': 0,
    '1': 100,
    '2': 255,
    '3': 475,
    '4': 770,
    '5': 1150,
    '6': 1625,
    '7': 2205,
    '8': 2900,
    '9': 3720,
    '10': 4675,
    '11': 5775,
    '12': 7030,
    '13': 8450,
    '14': 10045,
    '15': 11825,
    '16': 13800,
    '17': 15980,
    '18': 18375,
    '19': 20995,
    '20': 23850,
    '21': 26950,
    '22': 30305,
    '23': 33925,
    '24': 37820,
    '25': 42000,
    '26': 46475,
    '27': 51255,
    '28': 56350,
    '29': 61770,
    '30': 67525,
    '31': 73625,
    '32': 80080,
    '33': 86900,
    '34': 94095,
    '35': 101675,
    '36': 109650,
    '37': 118030,
    '38': 126825,
    '39': 136045,
    '40': 145700,
    '41': 155800,
    '42': 166355,
    '43': 177375,
    '44': 188870,
    '45': 200850,
    '46': 213325,
    '47': 226305,
    '48': 239800,
    '49': 253820,
    '50': 268375,
    '51': 283475,
    '52': 299130,
    '53': 315350,
    '54': 332145,
    '55': 349525,
    '56': 367500,
    '57': 386080,
    '58': 405275,
    '59': 425095,
    '60': 445550,
    '61': 466650,
    '62': 488405,
    '63': 510825,
    '64': 533920,
    '65': 557700,
    '66': 582175,
    '67': 607355,
    '68': 633250,
    '69': 659870,
    '70': 687225,
    '71': 715325,
    '72': 744180,
    '73': 773800,
    '74': 804195,
    '75': 835375,
    '76': 867350,
    '77': 900130,
    '78': 933725,
    '79': 968145,
    '80': 1003400,
    '81': 1039500,
    '82': 1076455,
    '83': 1114275,
    '84': 1152970,
    '85': 1192550,
    '86': 1233025,
    '87': 1274405,
    '88': 1316700,
    '89': 1359920,
    '90': 1404075,
    '91': 1449175,
    '92': 1495230,
    '93': 1542250,
    '94': 1590245,
    '95': 1639225,
    '96': 1689200,
    '97': 1740180,
    '98': 1792175,
    '99': 1845195,
    '100': 1899250
}

SUPER_SCRIPTS=["⁰","¹","²","³","⁴","⁵","⁶", "⁷","⁸", "⁹"]

DARK_ELIXIR = ["Minion", "Hog Rider", "Valkyrie", "Golem", "Witch", "Lava Hound", "Bowler", "Ice Golem", "Headhunter"]
SUPER_TROOPS = ["Super Barbarian", "Super Archer", "Super Giant", "Sneaky Goblin", "Super Wall Breaker", "Rocket Balloon", "Super Wizard", "Inferno Dragon",
                "Super Minion", "Super Valkyrie", "Super Witch", "Ice Hound", "Super Bowler", "Super Dragon", "Super Miner"]

leagues = ["Legend League", "Titan League I" , "Titan League II" , "Titan League III" ,"Champion League I", "Champion League II", "Champion League III",
                   "Master League I", "Master League II", "Master League III",
                   "Crystal League I","Crystal League II", "Crystal League III",
                   "Gold League I","Gold League II", "Gold League III",
                   "Silver League I","Silver League II","Silver League III",
                   "Bronze League I", "Bronze League II", "Bronze League III", "Unranked"]

ROLES = ["Member", "Elder", "Co-Leader", "Leader"]

war_leagues = json.load(open(f"Assets/war_leagues.json"))