#!/usr/bin/env python3
import os  # noqa

import discord  # noqa
from dotenv import load_dotenv  # noqa

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


client.run(TOKEN)
