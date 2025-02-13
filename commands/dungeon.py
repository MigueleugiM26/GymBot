import discord
import json
import random
import asyncio
from discord.ui import View, Button
from discord.app_commands import command
from discord import Message
from commands.globalFunctions import load_user_data, save_user_data
from datetime import datetime, timedelta

with open("storage/shopTable.json", "r") as file:
    shop_data = json.load(file)

with open("storage/itemTable.json", "r") as file:
    item_data = json.load(file)


def generate_health_bar(current_hp, bar_length=10):
    filled_length = round(bar_length * current_hp / max_hp) 
    empty_length = bar_length - filled_length
    return "🟥" * filled_length + "⬛" * empty_length

class TimeoutManager:
    _tasks = {}
    _last_activity = {}

    @classmethod
    def record_activity(cls, user_id):
        cls._last_activity[user_id] = datetime.now()

    @classmethod
    async def start_global_timer(cls, user_id, user_entry, message_id, enemy_name, enemy_stats, interaction, client):
        if user_id in cls._tasks:
            cls._tasks[user_id].cancel()

        cls.record_activity(user_id) 
        print(f"Recorded activity for {user_id}: {cls._last_activity[user_id]}")

        async def inactivity_checker():
            try:
                while True:
                    await asyncio.sleep(5)  # Check every 5 seconds
                    print(f"Recorded activity for {user_id}: {cls._last_activity[user_id]}")
                    if user_id not in cls._last_activity:
                        print(f"User {user_id} has no recorded activity. Exiting checker.")
                        return  

                    last_activity = cls._last_activity[user_id]
                    if datetime.now() - last_activity >= timedelta(seconds=10):  # inactivity time
                        print(f"Disabling.")                        

                        embed = discord.Embed(
                            title=f"The {enemy_name} defeats you!",
                            description="You took too long to act!",
                            color=discord.Color.dark_red()
                        )
                        embed.set_thumbnail(url=enemy_stats["image"])

                        embed.add_field(name="", value=f"You have fallen! The gym quickly calls an ambulance!", inline=False)

                        message = await cls.fetch_message_by_id(message_id, client)
                        await message.edit(embed=embed, view=None)
                        cls.cancel_timer(user_id)
                        break 
            except asyncio.CancelledError:
                pass 

        cls._tasks[user_id] = asyncio.create_task(inactivity_checker())

    @classmethod
    async def fetch_message_by_id(cls, message_id, client):
        channel = await client.fetch_channel('1180945248709517385') 
        message = await channel.fetch_message(message_id)
        return message

    @classmethod
    def cancel_timer(cls, user_id):
        if user_id in cls._tasks:
            cls._tasks[user_id].cancel()
            del cls._tasks[user_id]
        cls._last_activity.pop(user_id, None)


class ReviveView(View):
    def __init__(self, user_entry, enemy_name, enemy_stats, statuses, interaction):
        super().__init__()
        self.user_entry = user_entry
        self.enemy_name = enemy_name
        self.enemy_stats = enemy_stats
        self.statuses = statuses
        self.interaction = interaction

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.danger)
    async def continue_button(self, interaction: discord.Interaction, button: Button):
        health_bar = generate_health_bar(self.user_entry["hp"])

        embed = discord.Embed(
            title=f"{interaction.user.display_name} vs **{self.enemy_name}**",
            description=f"{interaction.user.display_name} won't go down!",
            color=discord.Color.red()
        )

        for status_key, is_active in self.statuses.items():
            if status_key == "hasStatus":
                continue

            if is_active: 
                formatted_status = status_key.replace("has", "").replace("Cramps", " Cramps")
                embed.add_field(name="", value=f"You are afflicted by **{formatted_status.strip()}**!", inline=False)

        embed.set_thumbnail(url=self.enemy_stats["image"])
        embed.add_field(name="Your stats:", value=f"**HP**: {self.user_entry['hp']} {health_bar}", inline=False)

        strength_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasDisease"] else ""
        agility_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasExhaustion"] else ""
        endurance_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasFatigue"] else ""
        flexibility_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasStiffness"] else ""
        embed.add_field(
        name="",
        value=(
            f"**Strength**: {self.user_entry['strength']} {strength_debuff}  |  **Agility**: {self.user_entry['agility']} {agility_debuff}\n"
            f"**Endurance**: {self.user_entry['endurance']} {endurance_debuff}  |  **Flexibility**: {self.user_entry['flexibility']} {flexibility_debuff}"
        ),
        inline=False
        )

        view = PlayerView(self.user_entry, self.enemy_name, self.enemy_stats, self.statuses, interaction)
        await interaction.message.edit(embed=embed, view=view)
        
        if not interaction.response.is_done():
            await interaction.response.defer()


class ConsumableButton(Button):
    def __init__(self, user_entry, enemy_name, enemy_stats, statuses, item_name, quantity, interaction, style):
        super().__init__(label=f"{item_name.title()}", style=style)
        self.user_entry = user_entry
        self.enemy_name = enemy_name
        self.enemy_stats = enemy_stats
        self.statuses = statuses
        self.item_name = item_name
        self.quantity = quantity
        self.interaction = interaction

    async def callback(self, interaction: discord.Interaction):
        item_details = item_data.get(self.item_name)
        if not item_data:
            await interaction.response.send_message(f"Item details for {self.item_name} are missing!", ephemeral=True)
            return
        
        item_type = item_details[0]
        stat = item_details[1]
        value = int(item_details[2]) if len(item_details) > 2 else None

        embed = discord.Embed(
                title=f"",
                description="",
                color=discord.Color.red()
            )
        
        if item_type == "boost":
            if stat == "hp":
                current_hp = self.user_entry.get("hp", 0)
                new_hp = min(current_hp + value, max_hp)
                self.user_entry["hp"] = new_hp
                embed.title = f"You used **{self.item_name.title()}**."
                embed.description = f"You recovered {value} HP."
            else:
                current_stat = self.user_entry.get(stat, 0)
                self.user_entry[stat] = current_stat + value
                embed.title = f"You used **{self.item_name.title()}**."
                embed.description = f"Your {stat.title()} increased by {value}."
        elif item_type == "status":
            self.statuses["hasStatus"] = False
            statBool = stat.title()
            statBool = statBool.replace(" ", "")

            status_type_key = f"has{statBool}"
            if status_type_key in self.statuses:
                self.statuses[status_type_key] = False

            match stat:
                case "disease":
                    self.user_entry["strength"] += self.statuses["debuffValue"]
                    self.statuses["debuffValue"] = 0   
                case "exhaustion":
                    self.user_entry["agility"] = self.statuses["debuffValue"]
                    self.statuses["debuffValue"] = 0                     
                case "fatigue":
                    self.user_entry["endurance"] += self.statuses["debuffValue"]
                    self.statuses["debuffValue"] = 0     
                    
                case "stiffness":
                    self.user_entry["flexibility"] += self.statuses["debuffValue"]
                    self.statuses["debuffValue"] = 0    
                    
            embed.title = f"You used **{self.item_name.title()}**."
            embed.description = f"It clears **{stat.replace('_', ' ').title()}**."
        else:
            await interaction.response.send_message(
                f"**{self.item_name.title()}** is an unknown type of item.",
                ephemeral=True
            )

        embed.set_thumbnail(url=self.enemy_stats["image"])
        embed.add_field(name="", value=f"It's the {self.enemy_name}'s turn!", inline=False)


        inventory = self.user_entry.get("inventory", {})
        if self.item_name in inventory:
            inventory[self.item_name][1] -= 1 
            if inventory[self.item_name][1] <= 0:
                del inventory[self.item_name]

        user_data = load_user_data()
        user_id = str(interaction.user.id) 
        user_data[user_id]["inventory"] = inventory  
        save_user_data(user_data)

        view = EnemyView(self.user_entry, self.enemy_name, self.enemy_stats, self.statuses, self.interaction)
        await interaction.message.edit(embed=embed, view=view)

        if not interaction.response.is_done():
            await interaction.response.defer()


class InventoryView(View):
    def __init__(self, user_entry, enemy_name, enemy_stats, statuses, interaction):
        super().__init__()
        self.user_entry = user_entry
        self.enemy_name = enemy_name
        self.enemy_stats = enemy_stats
        self.statuses = statuses
        self.interaction = interaction

        self.add_consumable_buttons()

    def add_consumable_buttons(self):
        inventory = self.user_entry.get("inventory", {})
        consumables = {
            item_name: details
            for item_name, details in inventory.items()
            if details[0] == "c" 
        }

        for item_name, details in consumables.items():
            item_details = item_data.get(item_name)
            if item_details[0] == "boost":
                button_label = f"{item_name.title()})" 
                self.add_item(ConsumableButton(self.user_entry, self.enemy_name, self.enemy_stats, self.statuses, item_name, details[1], self.interaction, discord.ButtonStyle.green))
            elif item_details[0] == "status":
                status = item_details[1] 
                statBool = status.title()
                statBool = statBool.replace(" ", "")
                if self.statuses.get(f"has{statBool}", False):
                    button_label = f"{item_name.title()}"
                    self.add_item(ConsumableButton(self.user_entry, self.enemy_name, self.enemy_stats, self.statuses, item_name, details[1], self.interaction, discord.ButtonStyle.blurple))

    @discord.ui.button(label="< Back", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction:discord.Interaction, button: Button):
        health_bar = generate_health_bar(self.user_entry["hp"])

        embed = discord.Embed(
            title=f"{interaction.user.display_name} vs **{self.enemy_name}**",
            description=f"",
            color=discord.Color.red()
        )

        embed.set_thumbnail(url=self.enemy_stats["image"])
        embed.add_field(name=f"", value=f"It's your turn", inline=False)
        for status_key, is_active in self.statuses.items():
            if status_key == "hasStatus":
                continue

            if status_key == "debuffValue":
                continue
    
            if is_active: 
                formatted_status = status_key.replace("has", "").replace("Cramps", " Cramps")
                embed.add_field(name="", value=f"You are afflicted by **{formatted_status.strip()}**!", inline=False)
        embed.add_field(name=f"Your stats:", value=f"**HP**: {self.user_entry['hp']} {health_bar}", inline=False)

        strength_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasDisease"] else ""
        agility_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasExhaustion"] else ""
        endurance_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasFatigue"] else ""
        flexibility_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasStiffness"] else ""
        embed.add_field(
        name="",
        value=(
            f"**Strength**: {self.user_entry['strength']} {strength_debuff}  |  **Agility**: {self.user_entry['agility']} {agility_debuff}\n"
            f"**Endurance**: {self.user_entry['endurance']} {endurance_debuff}  |  **Flexibility**: {self.user_entry['flexibility']} {flexibility_debuff}"
        ),
        inline=False
        )

        view = PlayerView(self.user_entry, self.enemy_name, self.enemy_stats, self.statuses, self.interaction)
        await interaction.message.edit(embed=embed, view=view)

        if not interaction.response.is_done():
            await interaction.response.defer()


class EnemyView(View):
    def __init__(self, user_entry, enemy_name, enemy_stats, statuses, interaction):
        super().__init__()
        self.user_entry = user_entry
        self.enemy_name = enemy_name
        self.enemy_stats = enemy_stats
        self.statuses = statuses
        self.interaction = interaction

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.danger)
    async def continue_button(self, interaction: discord.Interaction, button: Button):
        evasionChance = 5 + (self.enemy_stats["precision"] - self.user_entry["flexibility"])
        evasionChance = max(5, min(90, evasionChance))

        randomRoll = random.randint(0, 100)

        if randomRoll <= evasionChance:
            health_bar = generate_health_bar(self.user_entry["hp"])

            embed = discord.Embed(
                title=f"{interaction.user.display_name} vs **{self.enemy_name}**",
                description=f"",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=self.enemy_stats["image"])
            embed.add_field(name=f"You dodged the **{self.enemy_name}**'s attack!", value=f"It's your turn", inline=False)
            for status_key, is_active in self.statuses.items():
                if status_key == "hasStatus":
                    continue

                if status_key == "debuffValue":
                    continue
        
                if is_active: 
                    formatted_status = status_key.replace("has", "").replace("Cramps", " Cramps")
                    embed.add_field(name="", value=f"You are afflicted by **{formatted_status.strip()}**!", inline=False)

            embed.add_field(name=f"Your stats:", value=f"**HP**: {self.user_entry['hp']} {health_bar}", inline=False)

            strength_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasDisease"] else ""
            agility_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasExhaustion"] else ""
            endurance_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasFatigue"] else ""
            flexibility_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasStiffness"] else ""
            embed.add_field(
            name="",
            value=(
                f"**Strength**: {self.user_entry['strength']} {strength_debuff}  |  **Agility**: {self.user_entry['agility']} {agility_debuff}\n"
                f"**Endurance**: {self.user_entry['endurance']} {endurance_debuff}  |  **Flexibility**: {self.user_entry['flexibility']} {flexibility_debuff}"
            ),
            inline=False
            )

            view = PlayerView(self.user_entry, self.enemy_name, self.enemy_stats, self.statuses, self.interaction)
            await interaction.message.edit(embed=embed, view=view)
        else:
            if self.statuses["hasStatus"] or random.randint(0, 100) <= 85 or "skills" not in self.enemy_stats: # Normal Attack
                baseDamage = self.enemy_stats["attack"]

                critical = False

                if random.randint(0, 100) <= 5:
                    baseDamage = baseDamage * 2
                    critical = True

                self.user_entry["hp"] -= baseDamage
                if self.statuses["hasBurning"]:
                    burningDamage = max(0.5, self.enemy_stats["attack"]/4)
                    self.user_entry["hp"] -= burningDamage
                self.user_entry["hp"] = max(0, self.user_entry["hp"])

                if self.user_entry["hp"] <= 0:
                    reviveChance = max(20, self.user_entry["endurance"] / 10)

                    randomRoll = random.randint(0, 100)

                    if randomRoll <= reviveChance:
                        self.user_entry["hp"] += 1

                        embed = discord.Embed (
                            title=f"The **{self.enemy_name}** has attacked you!",
                            color=discord.Color.red()
                        )
                        embed.set_thumbnail(url=self.enemy_stats["image"])
                        if critical:
                            embed.add_field(name="", value=f"**Critical hit!** You suffer {baseDamage} damage!", inline=False)
                        else:
                            embed.add_field(name="", value=f"You suffer {baseDamage} damage!", inline=False)
                        if self.statuses["hasBurning"]:
                            embed.add_field(name="", value=f"You also suffer {burningDamage} burning damage!", inline=False)
                        embed.add_field(name="", value=f"The **{self.enemy_name}** has knocked you down, but your muscles won't give up! You recover 1 HP!", inline=False)
                        view = ReviveView(self.user_entry, self.enemy_name, self.enemy_stats, self.statuses, self.interaction)
                        await interaction.message.edit(embed=embed, view=view)
                    else:      
                        embed = discord.Embed (
                            title=f"The **{self.enemy_name}** has attacked you!",
                            color=discord.Color.red()
                        )
                        embed.set_thumbnail(url=self.enemy_stats["image"])
                        if critical:
                            embed.add_field(name="", value=f"**Critical hit!** You suffer {baseDamage} damage!", inline=False)
                        else:
                            embed.add_field(name="", value=f"You suffer {baseDamage} damage!", inline=False)
                        if self.statuses["hasBurning"]:
                            embed.add_field(name="", value=f"You also suffer {burningDamage} burning damage!", inline=False)
                        embed.add_field(name="", value=f"You have fallen! The gym quickly calls an ambulance!", inline=False)

                        player_inventory = self.user_entry.setdefault("inventory", {})
                        gold_loot_info = self.enemy_stats["loot"].get("gold", [])
                        base_gold = gold_loot_info[2]

                        gold_loss = random.randint(base_gold // 2, base_gold * 2)

                        current_gold = player_inventory.get("gold", ["g", 0])[1]
                        gold_after_loss = max(0, current_gold - gold_loss)  

                        player_inventory["gold"] = ["g", gold_after_loss]

                        embed.add_field(name="", value=f"You had to pay {gold_loss} gold in healthcare.", inline=False)

                        user_data = load_user_data()
                        user_id = str(interaction.user.id) 
                        user_data[user_id].setdefault("inventory", {}).update(self.user_entry.get("inventory", {}))
                        save_user_data(user_data)

                        await interaction.message.edit(embed=embed, view=None)
                else:
                    health_bar = generate_health_bar(self.user_entry["hp"])

                    embed = discord.Embed(
                        title=f"{interaction.user.display_name} vs **{self.enemy_name}**",
                        description=f"",
                        color=discord.Color.red()
                    )
                    embed.set_thumbnail(url=self.enemy_stats["image"])

                    burningString = ""
                    if self.statuses["hasBurning"]:
                        burningString = f"\nYou also suffer {burningDamage} burning damage!"

                    if critical:
                        embed.add_field(name=f"The **{self.enemy_name}** has attacked you!", value=f"**Critical hit!** You suffer {baseDamage} damage!{burningString}", inline=False)
                    else:
                        embed.add_field(name=f"The **{self.enemy_name}** has attacked you!", value=f"You suffer {baseDamage} damage!{burningString}", inline=False)
                    
                    for status_key, is_active in self.statuses.items():
                        if status_key == "hasStatus":
                            continue

                        if status_key == "debuffValue":
                            continue

                        if is_active: 
                            formatted_status = status_key.replace("has", "").replace("Cramps", " Cramps")
                            embed.add_field(name="", value=f"You are afflicted by **{formatted_status.strip()}**!", inline=False)
                    embed.add_field(name=f"Your stats:", value=f"**HP**: {self.user_entry['hp']} {health_bar}", inline=False)

                    strength_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasDisease"] else ""
                    agility_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasExhaustion"] else ""
                    endurance_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasFatigue"] else ""
                    flexibility_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasStiffness"] else ""
                    embed.add_field(
                    name="",
                    value=(
                        f"**Strength**: {self.user_entry['strength']} {strength_debuff}  |  **Agility**: {self.user_entry['agility']} {agility_debuff}\n"
                        f"**Endurance**: {self.user_entry['endurance']} {endurance_debuff}  |  **Flexibility**: {self.user_entry['flexibility']} {flexibility_debuff}"
                    ),
                    inline=False
                    )

                    view = PlayerView(self.user_entry, self.enemy_name, self.enemy_stats, self.statuses, self.interaction)
                    await interaction.message.edit(embed=embed, view=view)
            else: # Use Skill
                skill_name, skill_data = None, None
                if "skills" in self.enemy_stats:
                    total_chance = sum(int(data[0]) for data in self.enemy_stats["skills"].values())
                    random_roll = random.randint(1, total_chance)
                    cumulative_chance = 0
                    for name, data in self.enemy_stats["skills"].items():
                        cumulative_chance += int(data[0])
                        if random_roll <= cumulative_chance:
                            skill_name, skill_data = name, data
                            break
                
                if skill_name and skill_data:
                    skill_description = skill_data[1]
                    skill_type = skill_data[2]
                    skill_effect = skill_data[3]

                    if skill_type == "damage":
                        skill_effect = int(skill_data[3])
                        baseDamage = self.enemy_stats["attack"] + skill_effect
                        self.user_entry["hp"] = max(0, self.user_entry["hp"] - baseDamage)
                    elif skill_type == "ailment":
                        statBool = skill_effect.title()
                        statBool = statBool.replace(" ", "")
                        status_key = f"has{statBool}"
                        if status_key in self.statuses:
                            self.statuses[status_key] = True
                        self.statuses["hasStatus"] = True  
                         
                        match skill_effect:
                            case "disease":
                                self.statuses["debuffValue"] = 25 * self.user_entry["strength"] / 100    
                                self.user_entry["strength"] -= self.statuses["debuffValue"]
                            case "exhaustion":
                                self.statuses["debuffValue"] = 25 * self.user_entry["agility"] / 100    
                                self.user_entry["agility"] -= self.statuses["debuffValue"]
                            case "fatigue":
                                self.statuses["debuffValue"] = 25 * self.user_entry["endurance"] / 100    
                                self.user_entry["endurance"] -= self.statuses["debuffValue"]
                            case "stiffness":
                                self.statuses["debuffValue"] = 25 * self.user_entry["flexibility"] / 100    
                                self.user_entry["flexibility"] -= self.statuses["debuffValue"]

                if self.user_entry["hp"] <= 0:
                    reviveChance = max(20, self.user_entry["endurance"] / 10)

                    randomRoll = random.randint(0, 100)

                    if randomRoll <= reviveChance:
                        self.user_entry["hp"] += 1

                        embed = discord.Embed (
                            title=f"The **{self.enemy_name}** has used **{skill_name}**!",
                            color=discord.Color.red()
                        )
                        embed.add_field(name="", value=skill_description, inline=False)
                        embed.set_thumbnail(url=self.enemy_stats["image"])
                        if skill_type == "damage":
                            embed.add_field(name="", value=f"You suffer {baseDamage} damage!", inline=False)
                        elif skill_type == "ailment":
                            embed.add_field(name="", value=f"You are afflicted by **{skill_name}**!", inline=False)
                        embed.add_field(name="", value=f"The **{self.enemy_name}** has knocked you down, but your muscles won't give up! You recover 1 HP!", inline=False)
                        view = ReviveView(self.user_entry, self.enemy_name, self.enemy_stats, self.statuses, self.interaction)
                        await interaction.message.edit(embed=embed, view=view)
                    else:      
                        embed = discord.Embed (
                            title=f"The **{self.enemy_name}** has used **{skill_name}**!",
                            color=discord.Color.red()
                        )

                        embed.add_field(name="", value=skill_description, inline=False)
                        embed.set_thumbnail(url=self.enemy_stats["image"])
                        if skill_type == "damage":
                            embed.add_field(name="", value=f"You suffer {baseDamage} damage!", inline=False)
                        elif skill_type == "ailment":
                            embed.add_field(name="", value=f"You are afflicted by **{skill_name}**!", inline=False)
                        embed.add_field(name="", value=f"You have fallen! The gym quickly calls an ambulance!", inline=False)

                        player_inventory = self.user_entry.setdefault("inventory", {})
                        gold_loot_info = self.enemy_stats["loot"].get("gold", [])
                        base_gold = gold_loot_info[2]

                        gold_loss = random.randint(base_gold // 2, base_gold * 2)

                        current_gold = player_inventory.get("gold", ["g", 0])[1]
                        gold_after_loss = max(0, current_gold - gold_loss)  

                        player_inventory["gold"] = ["g", gold_after_loss]

                        embed.add_field(name="", value=f"You had to pay {gold_loss} gold in healthcare.", inline=False)

                        user_data = load_user_data()
                        user_id = str(interaction.user.id) 
                        user_data[user_id].setdefault("inventory", {}).update(self.user_entry.get("inventory", {}))
                        save_user_data(user_data)

                        await interaction.message.edit(embed=embed, view=None)
                else:
                    health_bar = generate_health_bar(self.user_entry["hp"])

                    embed = discord.Embed(
                        title=f"{interaction.user.display_name} vs **{self.enemy_name}**",
                        description=f"",
                        color=discord.Color.red()
                    )
                    embed.set_thumbnail(url=self.enemy_stats["image"])
                    if skill_type == "damage":
                        embed.add_field(name=f"{skill_description}", value=f"You suffer {baseDamage} damage!", inline=False)
                    elif skill_type == "ailment":
                        embed.add_field(name=f"{skill_description}", value=f"You are afflicted by **{skill_effect}**!", inline=False)

                    embed.add_field(name=f"Your stats:", value=f"**HP**: {self.user_entry['hp']} {health_bar}", inline=False)

                    strength_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasDisease"] else ""
                    agility_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasExhaustion"] else ""
                    endurance_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasFatigue"] else ""
                    flexibility_debuff = f" (-{self.statuses["debuffValue"]})" if self.statuses["hasStiffness"] else ""
                    embed.add_field(
                    name="",
                    value=(
                        f"**Strength**: {self.user_entry['strength']} {strength_debuff}  |  **Agility**: {self.user_entry['agility']} {agility_debuff}\n"
                        f"**Endurance**: {self.user_entry['endurance']} {endurance_debuff}  |  **Flexibility**: {self.user_entry['flexibility']} {flexibility_debuff}"
                    ),
                    inline=False
                    )

                    view = PlayerView(self.user_entry, self.enemy_name, self.enemy_stats, self.statuses, self.interaction)
                    await interaction.message.edit(embed=embed, view=view)

        if not interaction.response.is_done():
            await interaction.response.defer()


class PlayerView(View):
    def __init__(self, user_entry, enemy_name, enemy_stats, statuses, interaction):
        super().__init__()
        self.user_entry = user_entry
        self.enemy_name = enemy_name
        self.enemy_stats = enemy_stats
        self.statuses = statuses
        self.interaction = interaction

        self.skills_button.disabled = self.statuses.get("hasMuscleCramps", False)


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        user_id = interaction.user.id
        TimeoutManager.record_activity(user_id)     
        return True
        
    @discord.ui.button(label="Punch", style=discord.ButtonStyle.danger)
    async def attack_button(self, interaction: discord.Interaction, button: Button):
        evasionChance = 5 + (self.user_entry["agility"] - self.enemy_stats["evasion"])
        evasionChance = max(5, min(90, evasionChance))

        randomRoll = random.randint(0, 100)

        if randomRoll <= evasionChance:
            embed = discord.Embed (
                title=f"The **{self.enemy_name}** dodged your punch!",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=self.enemy_stats["image"])
            embed.add_field(name="", value=f"It's the {self.enemy_name}'s turn!")
            view = EnemyView(self.user_entry, self.enemy_name, self.enemy_stats, self.statuses, self.interaction)
            await interaction.message.edit(embed=embed, view=view)
        else:
            if self.statuses["hasDisorientation"] and random.randint(0, 100) <= 75:
                self.user_entry["hp"] -= max(1, self.enemy_stats["attack"]/2)
                self.user_entry["hp"] = max(1, self.user_entry["hp"])

                embed = discord.Embed (
                    title=f"You are disoriented, and you punch yourself!",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=self.enemy_stats["image"])
                embed.add_field(name="", value=f"You suffer {max(1, self.enemy_stats["attack"]/2)} damage!", inline=False)
                embed.add_field(name="", value=f"It's the {self.enemy_name}'s turn!", inline=False)
                view = EnemyView(self.user_entry, self.enemy_name, self.enemy_stats, self.statuses, self.interaction)
                await interaction.message.edit(embed=embed, view=view)

                if not interaction.response.is_done():
                    await interaction.response.defer()

                return


            baseDamage = self.user_entry['strength'] - ((self.enemy_stats["defense"] * random.randint(1, 3)) / 2)
            baseDamage = max(1, baseDamage)  
            critical = False

            if random.randint(0, 100) <= 5:
                baseDamage += 25 * baseDamage /100
                critical = True

            self.enemy_stats["hp"] -= baseDamage

            if self.enemy_stats["hp"] <= 0:
                embed = discord.Embed (
                    title=f"You punch the **{self.enemy_name}**!",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=self.enemy_stats["image"])
                if critical:
                    embed.add_field(name="", value=f"**Critical hit!** You deal {baseDamage} damage!", inline=False)
                else:
                    embed.add_field(name="", value=f"You deal {baseDamage} damage!", inline=False)
                
                embed.add_field(name="", value=f"The {self.enemy_name} has been defeated!", inline=False)

                loot = self.enemy_stats.get("loot", {})
                player_inventory = self.user_entry.setdefault("inventory", {})
                loot_messages = []

                for item, (type, chance, value) in loot.items():
                    if random.randint(1, 100) <= chance: 
                        if item == "gold":
                            item_dropped = max(1, random.randint(value // 2, value))
                        else:
                            item_dropped = max(1, random.randint(1, value))
                        if item not in player_inventory:
                            player_inventory[item] = [type, item_dropped]
                        else:
                            player_inventory[item][1] += item_dropped
                        loot_messages.append(f"You found {item_dropped} {item}!")

                if loot_messages:
                    embed.add_field(name="Loot", value="\n".join(loot_messages), inline=False)
                else:
                    embed.add_field(name="Loot", value="You found nothing!", inline=False)

                user_data = load_user_data()
                user_id = str(interaction.user.id) 
                user_data[user_id].setdefault("inventory", {}).update(self.user_entry.get("inventory", {}))
                save_user_data(user_data)

                await interaction.message.edit(embed=embed, view=None)
            else:
                embed = discord.Embed (
                    title=f"You punch the **{self.enemy_name}**!",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=self.enemy_stats["image"])
                if critical:
                    embed.add_field(name="", value=f"**Critical hit!** You deal {baseDamage} damage!", inline=False)
                else:
                    embed.add_field(name="", value=f"You deal {baseDamage} damage!", inline=False)
                embed.add_field(name="", value=f"It's the {self.enemy_name}'s turn!", inline=False)
                view = EnemyView(self.user_entry, self.enemy_name, self.enemy_stats, self.statuses, self.interaction)
                await interaction.message.edit(embed=embed, view=view)

        if not interaction.response.is_done():
            await interaction.response.defer()

    @discord.ui.button(label="Skills", style=discord.ButtonStyle.primary)
    async def skills_button(self, interaction: discord.Interaction, button: Button):

        await interaction.response.send_message(f"You prepare a skill against the **{self.enemy_name}**!", ephemeral=True)

    @discord.ui.button(label="Inventory", style=discord.ButtonStyle.green)
    async def inventory_button(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
                title=f"Inventory",
                description="",
                color=discord.Color.green()
            )
        inventory = self.user_entry.get("inventory", {})
        consumables = []
        for level, items in shop_data.items():
            for item_name, item_details in items.items():
                if item_name in inventory and item_details[0] == "c":
                    consumables.append(f"**{inventory[item_name][1]}x {item_name.title()}** \n{item_details[2]}\n")
        if consumables:
            embed.add_field(name="", value="\n".join(consumables), inline=False)
        else:
            embed.add_field(name="", value="You have no items.", inline=False)

        view = InventoryView(self.user_entry, self.enemy_name, self.enemy_stats, self.statuses, self.interaction)
        await interaction.message.edit(embed=embed, view=view)

        if not interaction.response.is_done():
            await interaction.response.defer()

    @discord.ui.button(label="Flee", style=discord.ButtonStyle.gray)
    async def flee_button(self, interaction: discord.Interaction, button: Button):
        fleeChance = 5 + (self.user_entry["agility"] * 5 - self.enemy_stats["precision"])
        fleeChance = max(5, fleeChance)

        randomRoll = random.randint(0, 100)

        if randomRoll <= fleeChance:
            embed = discord.Embed(
                title=f"{interaction.user.display_name}, you fled from the **{self.enemy_name}**!",
                description="",
                color=discord.Color.light_gray()
            )

            await interaction.message.edit(embed=embed, view=None)
            self.stop() 
        else: 
            embed = discord.Embed (
                title=f"You couldn't flee!",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=self.enemy_stats["image"])
            embed.add_field(name="", value=f"It's the {self.enemy_name}'s turn!")
            view = EnemyView(self.user_entry, self.enemy_name, self.enemy_stats, self.statuses, self.interaction)
            await interaction.message.edit(embed=embed, view=view)
        if not interaction.response.is_done():
            await interaction.response.defer()


@command(name='dungeon', description='Adventure inside a dungeon.')
async def dungeon(interaction, level: int):
    with open("storage/enemies.json", "r") as file:
        enemies_data = json.load(file)

    if str(level) not in enemies_data:
        await interaction.response.send_message(f"Invalid dungeon level. Please choose a valid level.", ephemeral=True)
        return
    
    user_id = str(interaction.user.id) 
    user_data = load_user_data() 
    user_entry = user_data.get(user_id)

    if user_entry is None:
        await interaction.response.send_message(
            "You haven't gone to the gym yet.",
            ephemeral=True
        )
        return
    
    if user_entry["battles"] >= 20:
        await interaction.response.send_message(
            "You've used all of your energy today!",
            ephemeral=True
        )
        return
    
    user_data[user_id]["battles"] += 1  
    save_user_data(user_data)

    statuses = {
        "hasStatus": False,
        "hasExhaustion": False,
        "hasMuscleCramps": False,
        "hasStiffness": False,
        "hasBurning": False,
        "hasFatigue": False,
        "hasDisorientation": False,
        "hasDisease": False,
        "debuffValue": 0
    }

    level_enemies = enemies_data[str(level)]
    enemy_name, enemy_stats = random.choice(list(level_enemies.items()))  

    global max_hp
    max_hp = user_entry["hp"]
    health_bar = generate_health_bar(user_entry["hp"])

    embed = discord.Embed(
        title=f"{interaction.user.display_name}, you encounter a **{enemy_name}**!",
        description=f"",
        color=discord.Color.red()
    )
    embed.set_thumbnail(url=enemy_stats["image"])
    embed.add_field(name="Your stats:", value=f"**HP**: {user_entry['hp']} {health_bar}", inline=False)
    embed.add_field(
    name="",
    value=(
        f"**Strength**: {user_entry['strength']}  |  **Agility**: {user_entry['agility']}\n"
        f"**Endurance**: {user_entry['endurance']}  |  **Flexibility**: {user_entry['flexibility']}"
    ),
    inline=False
    )

    view = PlayerView(user_entry, enemy_name, enemy_stats, statuses, interaction)
    await interaction.response.defer()

    dungeon_message: Message = await interaction.followup.send(
        content=None,  
        embed=embed,
        view=view
    )

    message_id = dungeon_message.id
    await TimeoutManager.start_global_timer(user_id, user_entry, message_id, enemy_name, enemy_stats, interaction, interaction.client)

def setup(command_tree):
    command_tree.add_command(dungeon)
    dungeon.tree = command_tree