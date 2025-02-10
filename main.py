import discord
from commands.globalFunctions import load_user_data, save_user_data
from discord import app_commands
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os
from dotenv import load_dotenv

from commands import workout
from commands import dungeon
from commands import mirror
from commands import inventory
from commands import shop

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

workout.setup(tree)
dungeon.setup(tree)
mirror.setup(tree)
inventory.setup(tree)
shop.setup(tree)

    
def reset_daily_stats():
    user_data = load_user_data() 

    for user_id, user_entry in user_data.items():
        user_entry["hasRoutine"] = False
        user_entry["exercisesDone"] = 0
        user_entry["battles"] = 0

    save_user_data(user_data) 
    print("Daily stats reset.")  


@client.event
async def on_ready():
    try:
        guild = discord.Object(id=1180945248013254808)
        synced = await tree.sync()
        print(f"Synced {len(synced)} command(s) to the guild: {1180945248013254808}.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


    channel = client.get_channel(1180945248709517385)
    await channel.send("💪")
    print(f'Logged in as {client.user}')


scheduler = BackgroundScheduler()
scheduler.add_job(reset_daily_stats, CronTrigger(hour=0, minute=0, timezone="UTC"))
scheduler.start()

load_dotenv() 
client.run(os.getenv("BOT_TOKEN"))