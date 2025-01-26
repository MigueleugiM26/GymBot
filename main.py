import discord
from discord.ext import commands
from discord import app_commands

from commands import workout
from commands import mirror
from commands import ping
from commands import sync

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

workout.setup(tree)
mirror.setup(tree)
ping.setup(tree)
sync.setup(tree)

@client.event
async def on_ready():
    try:
        guild = discord.Object(id=1151266968163336273)
        synced = await tree.sync(guild=None)
        print(f"Synced {len(synced)} command(s) to the guild: {1151266968163336273}.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


    channel = client.get_channel(1330999204910465126)
    await channel.send("💪")
    print(f'Logged in as {client.user}')

client.run("MTMzMjgzODY2MTk4ODgxNDk0OQ.GBggky._N0G9cWXd-0C52iVFql12-BQtDIkND9ok3Xwe4")