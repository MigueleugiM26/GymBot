import discord
import json
import random
from discord.ui import View, Button
from discord.app_commands import command
from commands.globalFunctions import load_user_data, save_user_data

with open("storage/shopTable.json", "r") as file:
    shop_data = json.load(file)

with open("storage/itemTable.json", "r") as file:
    item_data = json.load(file)

class ShopView(View):
    def __init__(self, user_entry, user_id, available_items, interaction):
        super().__init__()
        self.user_entry = user_entry
        self.user_id = user_id
        self.interaction = interaction

        self.select = discord.ui.Select(
            placeholder="Select an item to buy",
            min_values=1,
            max_values=1,
            options=[discord.SelectOption(label=item, value=item) for item in available_items]
        )
        self.select.callback = self.select_item  
        self.add_item(self.select)

        self.sell_button = discord.ui.Button(label="Sell Loot", style=discord.ButtonStyle.green)
        self.sell_button.callback = self.sell_loot
        self.add_item(self.sell_button)
    
    async def select_item(self, interaction: discord.Interaction):      
        user_data = load_user_data()
        inventory = user_data[self.user_id]["inventory"]
        item_bought_price = 0

        item_name = self.select.values[0] 
        item_details = None
        for level_items in shop_data.values():
            if item_name in level_items:
                item_details = level_items[item_name]
                break

        if not item_details:
            await interaction.response.send_message("You already bought this item.", ephemeral=True)
            return

        item_type = item_details[0]
        price = item_details[1]  
        description = item_details[2]

        if inventory["gold"][1] < price:
            await interaction.response.send_message("You don't have enough gold to buy this item.", ephemeral=True)
            return

        item_bought_price = price
        inventory["gold"][1] -= price  
        if item_type == "e":  # Equipment 
            stat_to_increase = item_details[3]
            amount = int(item_details[4])

            user_data[self.user_id][stat_to_increase] += amount
            inventory[item_name] = (item_type, f"+{amount} {stat_to_increase}")

            for level_items in shop_data.values():
                if item_name in level_items:
                    del level_items[item_name] 
                    break

            self.select.options = [
                discord.SelectOption(label=item, value=item)
                for item in self.select.options
                if item.value != item_name
            ]

        elif item_type == "c":  # Consumable
            if item_name in inventory:
                inventory[item_name] = (item_type, inventory[item_name][1] + 1)
            else:
                inventory[item_name] = (item_type, 1)

        save_user_data(user_data)

        user_level = user_data[self.user_id]["level"]

        embed = discord.Embed(
            title="Shop",
            description="",
            color=discord.Color.blue()
        )

        embed.add_field(name="", value=f"💰 {interaction.user.display_name}, you have {inventory['gold'][1]} gold.", inline=False)

        shop_tiers = set()
        for index, (level, items) in enumerate(shop_data.items(), start=1):          
            if user_level >= int(level):
                shop_tiers.add(level)
                items_list = ""
                
                for item, details in items.items():
                    item_type = details[0]
                    price = details[1]
                    description = details[2]
                    
                    if item_type == "e" and item in self.user_entry["inventory"]:
                        continue  

                    items_list += f"**{item.title()}** \n{description} \n💰 {price} Gold\n\n"

                if items_list:
                    items_list += "\u200b"
                    embed.add_field(name=f"\n---------Shop Level {index}----------", value=items_list, inline=False)

        embed.add_field(name="\u200b", value="", inline=False)
        embed.set_footer(text=f"You bought a {item_name} for {item_bought_price} gold.") 

        await interaction.message.edit(embed=embed)

        if not interaction.response.is_done():
            await interaction.response.defer()


    async def sell_loot(self, interaction: discord.Interaction):
        user_data  = load_user_data()
        user_entry = user_data.get(self.user_id)

        if self.user_id not in user_data or "level" not in user_data[self.user_id]:
            await interaction.response.send_message("You haven't gone to the gym yet!", ephemeral=True)
            return
        
        inventory = user_data[self.user_id]["inventory"]
        gold = inventory["gold"][1]
        sellable_items = {item: count for item, (item_type, count) in inventory.items() if item_type == "s"}

        if not sellable_items:
            await interaction.response.send_message("You have no items to sell!", ephemeral=True)
            return
        
        total_value = 0
        for item, count in sellable_items.items():
            item_value = item_data.get(item, {}).get("value", 0)
            total_value += item_value * count

        total_value = int(total_value)
        inventory["gold"][1] += total_value

        for item in sellable_items:
            del inventory[item]

        save_user_data(user_data)

        user_level = user_data[self.user_id]["level"]
        embed = discord.Embed(
            title="Shop",
            description=f"",
            color=discord.Color.blue()
        )

        embed.add_field(name=f"", value=f"💰 {interaction.user.display_name}, you have {inventory['gold'][1]} gold.", inline=False)

        shop_tiers = set()  
        for index, (level, items) in enumerate(shop_data.items(), start=1):          
            if user_level >= int(level):
                shop_tiers.add(level)
                items_list = ""
                
                for item, details in items.items():
                    item_type = details[0]
                    price = details[1]
                    description = details[2]
                    
                    if item_type == "e" and item in user_entry["inventory"]:
                        continue  

                    items_list += f"**{item.title()}** \n{description} \n💰 {price} Gold\n\n"

                if items_list:
                    items_list += "\u200b"
                    embed.add_field(name=f"\n---------Shop Level {index}----------", value=items_list, inline=False)
                
        embed.add_field(name=f"\u200b", value=f"", inline=False)
        embed.set_footer(text = f"You sold your loot and earned {total_value} gold.")

        await interaction.message.edit(embed=embed)

        if not interaction.response.is_done():
            await interaction.response.defer()


@command(name='shop', description='Go to the shop.')
async def shop(interaction):
    user_id = str(interaction.user.id)
    user_data = load_user_data()
    user_entry = user_data.get(user_id)

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
    available_items = []

    for index, (level, items) in enumerate(shop_data.items(), start=1):          
        if user_level >= int(level):
            shop_tiers.add(level)
            items_list = ""
            
            for item, details in items.items():
                item_type = details[0]
                price = details[1]
                description = details[2]
                
                if item_type == "e" and item in user_entry["inventory"]:
                    continue  

                available_items.append(item)
                items_list += f"**{item.title()}** \n{description} \n💰 {price} Gold\n\n"

            if items_list:
                items_list += "\u200b"  
                embed.add_field(name=f"---------Shop Level {index}----------", value=items_list, inline=False)

    view = ShopView(user_entry, user_id, available_items, interaction)
    await interaction.response.send_message(embed=embed, view=view)


def setup(command_tree):
    command_tree.add_command(shop)
    shop.tree = command_tree
