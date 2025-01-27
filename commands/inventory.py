import discord
import json
import random
from discord.ui import View, Button
from discord.app_commands import command
from commands.globalFunctions import load_user_data


@command(name='inventory', description='View your inventory.')
async def inventory(interaction):
    user_id = str(interaction.user.id)
    user_data = load_user_data()

    if user_id not in user_data or "inventory" not in user_data[user_id]:
        await interaction.response.send_message("You haven't gone to a dungeon yet!", ephemeral=True)
        return

    inventory = user_data[user_id]["inventory"]
    gold = inventory.get("gold", [None, 0])[1] 

    consumables = {}
    equipment = {}
    sellables = {}

    for item, details in inventory.items():
        if isinstance(details, list) and len(details) == 2:
            item_type, quantity = details
            if item_type == "c":  # Consumables
                consumables[item] = quantity
            elif item_type == "e":  # Equipment
                equipment[item] = quantity
            elif item_type == "s":  # Sellables
                sellables[item] = quantity

    embed = discord.Embed(
        title=f"{interaction.user.display_name}'s Inventory",
        color=discord.Color.gold()
    )
    embed.add_field(name="Gold", value=f"💰 {gold}", inline=False)

    embed.add_field(name="\u200b", value="", inline=False) # spacing

    if consumables:
        consumables_text = "\n".join([f"**{item.title()}**: {quantity}" for item, quantity in consumables.items()])
        embed.add_field(name="Consumables", value=consumables_text, inline=False)
    else:
        embed.add_field(name="Consumables", value="You have no consumables!", inline=False)

    embed.add_field(name="\u200b", value="", inline=False) # spacing

    if equipment:
        equipment_text = "\n".join([f"**{item.title()}**: {quantity}" for item, quantity in equipment.items()])
        embed.add_field(name="Equipment", value=equipment_text, inline=False)
    else:
        embed.add_field(name="Equipment", value="You have no Equipment!", inline=False)

    embed.add_field(name="\u200b", value="", inline=False) # spacing

    if sellables:
        sellables_text = "\n".join([f"**{item.title()}**: {quantity}" for item, quantity in sellables.items()])
        embed.add_field(name="Sellables", value=sellables_text, inline=False)
    else:
        embed.add_field(name="Sellables", value="You have no sellable items!", inline=False)

    await interaction.response.send_message(embed=embed)


def setup(command_tree):
    command_tree.add_command(inventory)
    inventory.tree = command_tree
