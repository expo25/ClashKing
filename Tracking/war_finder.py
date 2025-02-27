import os
import time
from typing import Optional
from base64 import b64decode as base64_b64decode
from json import loads as json_loads
from datetime import datetime
from dotenv import load_dotenv
from msgspec.json import decode
from msgspec import Struct
from pymongo import UpdateOne
from datetime import timedelta
from asyncio_throttle import Throttler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc

import motor.motor_asyncio
import collections
import aiohttp
import asyncio
import coc
import string
import random

keys = []
load_dotenv()

client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("STATS_DB"))
looper = client.looper
clan_tags = looper.clan_tags
clan_wars = looper.clan_war

throttler = Throttler(rate_limit=1000, period=1)
scheduler = AsyncIOScheduler(timezone=utc)
scheduler.start()

emails = []
passwords = []
#26-29 (30)
for x in range(26,30):
    emails.append(f"apiclashofclans+test{x}@gmail.com")
    passwords.append(os.getenv("EMAIL_PW"))
coc_client = coc.Client(key_count=10, throttle_limit=25, cache_max_size=0, raw_attribute=True)

async def get_keys(emails: list, passwords: list, key_names: str, key_count: int):
    total_keys = []

    for count, email in enumerate(emails):
        _keys = []
        password = passwords[count]

        session = aiohttp.ClientSession()

        body = {"email": email, "password": password}
        resp = await session.post("https://developer.clashofclans.com/api/login", json=body)
        if resp.status == 403:
            raise RuntimeError(
                "Invalid Credentials"
            )

        resp_paylaod = await resp.json()
        ip = json_loads(base64_b64decode(resp_paylaod["temporaryAPIToken"].split(".")[1] + "====").decode("utf-8"))[
            "limits"][1]["cidrs"][0].split("/")[0]

        resp = await session.post("https://developer.clashofclans.com/api/apikey/list")
        keys = (await resp.json())["keys"]
        _keys.extend(key["key"] for key in keys if key["name"] == key_names and ip in key["cidrRanges"])

        for key in (k for k in keys if ip not in k["cidrRanges"]):
            await session.post("https://developer.clashofclans.com/api/apikey/revoke", json={"id": key["id"]})

        print(len(_keys))
        while len(_keys) < key_count:
            data = {
                "name": key_names,
                "description": "Created on {}".format(datetime.now().strftime("%c")),
                "cidrRanges": [ip],
                "scopes": ["clash"],
            }
            resp = await session.post("https://developer.clashofclans.com/api/apikey/create", json=data)
            key = await resp.json()
            _keys.append(key["key"]["key"])

        if len(keys) == 10 and len(_keys) < key_count:
            print("%s keys were requested to be used, but a maximum of %s could be "
                  "found/made on the developer site, as it has a maximum of 10 keys per account. "
                  "Please delete some keys or lower your `key_count` level."
                  "I will use %s keys for the life of this client.", )

        if len(_keys) == 0:
            raise RuntimeError(
                "There are {} API keys already created and none match a key_name of '{}'."
                "Please specify a key_name kwarg, or go to 'https://developer.clashofclans.com' to delete "
                "unused keys.".format(len(keys), key_names)
            )

        await session.close()
        #print("Successfully initialised keys for use.")
        for k in _keys:
            total_keys.append(k)

    print(len(total_keys))
    return (total_keys)

def create_keys():
    done = False
    while done is False:
        try:
            loop = asyncio.get_event_loop()
            keys = loop.run_until_complete(get_keys(emails=emails,
                                     passwords=passwords, key_names="test", key_count=10))
            done = True
            return keys
        except Exception as e:
            done = False
            print(e)

class Clan(Struct):
    tag: str
class War(Struct):
    state: str
    preparationStartTime: str
    endTime: str
    clan: Clan
    opponent: Clan

currently_in_war = set()
last_checked = {}
last_in_war = {}
to_check = set()


async def broadcast(keys):
    await asyncio.sleep(10)
    print("sleep")
    while True:
        async def fetch(url, session: aiohttp.ClientSession, headers, tag):
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return ((await response.read()), tag)
                elif response.status == 503:
                    return (503, 503)
                return (None, None)

        async def gather_with_concurrency(*tasks):
            async def sem_task(task):
                async with throttler:
                    return await task

            return await asyncio.gather(*(sem_task(task) for task in tasks), return_exceptions=True)

        global to_check
        all_tags = list(to_check)
        size_break = 50000
        all_tags = [all_tags[i:i + size_break] for i in range(0, len(all_tags), size_break)]

        for tag_group in all_tags:
            tasks = []
            connector = aiohttp.TCPConnector(limit=250, ttl_dns_cache=300)
            keys = collections.deque(keys)
            async with aiohttp.ClientSession(connector=connector) as session:
                for tag in tag_group:
                    keys.rotate(1)
                    tasks.append(fetch(f"https://api.clashofclans.com/v1/clans/{tag.replace('#', '%23')}/currentwar", session, {"Authorization": f"Bearer {keys[0]}"}, tag))
                responses = await gather_with_concurrency(*tasks)
                await session.close()

            changes = []
            for response, tag in responses: #type: bytes
                # we shouldnt have completely invalid tags, they all existed at some point
                if response is None or response == 503:
                    continue
                try:
                    war = decode(response, type=War)
                except:
                    continue
                if war.state != "notInWar":
                    war_end = coc.Timestamp(data=war.endTime)
                    run_time = war_end.time
                    if war_end.seconds_until < 0:
                        run_time = datetime.utcnow()
                    last_checked[tag] = time.time()
                    last_in_war[tag] = int(war_end.time.timestamp())
                    currently_in_war.add(tag)
                    to_check.remove(tag)
                    if war.state == "inWar":
                        print(war.clan.tag)
                    changes.append(UpdateOne({"war_id" : f"{tag}-{int(coc.Timestamp(data=war.preparationStartTime).time.timestamp())}"},
                                              {"$set": {
                                                  "clan" : war.clan.tag,
                                                  "opponent" : war.opponent.tag,
                                                  "endTime" : int(war_end.time.timestamp())
                                              }},
                                                upsert=True))
                    #schedule getting war
                    scheduler.add_job(store_war, 'date', run_date=run_time, args=[tag, int(coc.Timestamp(data=war.preparationStartTime).time.timestamp())],
                                      id=f"war_end_{tag}", name=f"{tag}_war_end", misfire_grace_time=3600)
            if changes:
                try:
                    results = await clan_wars.bulk_write(changes, ordered=False)
                    print(results.bulk_api_result)
                except:
                    pass

async def store_war(clan_tag: str, prep_time: int):
    found = False
    a_war = False
    while not found:
        try:
            war = await coc_client.get_clan_war(clan_tag=clan_tag)
            if (war.preparation_start_time.time.timestamp()) != prep_time:
                found = True
            elif war.state == "warEnded":
                found = True
                a_war = True
        except (coc.NotFound, coc.errors.Forbidden, coc.errors.PrivateWarLog):
            found = True
        except coc.errors.Maintenance:
            await asyncio.sleep(30)
        except Exception:
            found = True

    if not a_war:
        return

    source = string.ascii_letters
    custom_id = str(''.join((random.choice(source) for i in range(6)))).upper()
    is_used = await clan_wars.find_one({"custom_id": custom_id})
    while is_used is not None:
        custom_id = str(''.join((random.choice(source) for i in range(6)))).upper()
        is_used = await clan_wars.find_one({"custom_id": custom_id})
    last_checked[clan_tag] = time.time()
    await clan_wars.update_one({"war_id": f"{war.clan.tag}-{int(war.preparation_start_time.time.timestamp())}"}, {
        "custom_id": custom_id,
        "data": war._raw_data
    }, upsert=True)


loop = asyncio.get_event_loop()
keys = create_keys()
coc_client.login_with_keys(*keys[:10])
loop.create_task(broadcast(keys))
loop.run_forever()
