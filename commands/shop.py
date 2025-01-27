import discord
import json
import random
from discord.ui import View, Button
from discord.app_commands import command
from commands.globalFunctions import load_user_data

with open("storage/shopTable.json", "r") as file:
    shop_data = json.load(file)

@command(name='shop', description='Go to the shop.')
async def shop(interaction):
    user_id = str(interaction.user.id)
    user_data = load_user_data()

    if user_id not in user_data or "level" not in user_data[user_id]:
        await interaction.response.send_message("You haven't gone to the gym yet!", ephemeral=True)
        return
    
    user_level = user_data[user_id]["level"]  

    embed = discord.Embed(
        title="Shop",
        description=f"",
        color=discord.Color.blue()
    )

    embed.add_field(name=f"", value=f"💰 {interaction.user.display_name}, you have {user_data[user_id]["inventory"]["gold"][1]} gold.", inline=False)

    shop_tiers = set()  
    for level, items in shop_data.items():
        if user_level >= int(level): 
            shop_tiers.add(level)

            for item, details in items.items():
                item_type, price, description = details
                embed.add_field(name=f"", value=f"", inline=False)
                embed.add_field(name=f"**{item.title()}**", value=f"{description} \n💰 {price} Gold", inline=False)
                

    shop_level_count = len(shop_tiers)    
    embed.description = f"Shop Level {shop_level_count}"


    await interaction.response.send_message(embed=embed)


def setup(command_tree):
    command_tree.add_command(shop)
    shop.tree = command_tree
