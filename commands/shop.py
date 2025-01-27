import discord
import json
import random
from discord.ui import View, Button
from discord.app_commands import command
from commands.globalFunctions import load_user_data


@command(name='shop', description='Go to the shop.')
async def shop(interaction):
    await interaction.response.send_message("Command not ready.", ephemeral=True)


def setup(command_tree):
    command_tree.add_command(shop)
    shop.tree = command_tree
