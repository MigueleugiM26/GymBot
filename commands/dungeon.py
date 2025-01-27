import discord
import json
import random
from discord.ui import View, Button
from discord.app_commands import command
from commands.globalFunctions import load_user_data, save_user_data


with open("storage/enemies.json", "r") as file:
    enemies_data = json.load(file)


def generate_health_bar(current_hp, bar_length=10):
    filled_length = round(bar_length * current_hp / max_hp) 
    empty_length = bar_length - filled_length
    return "🟥" * filled_length + "⬛" * empty_length


class ReviveView(View):
    def __init__(self, user_entry, enemy_name, enemy_stats, interaction):
        super().__init__()
        self.user_entry = user_entry
        self.enemy_name = enemy_name
        self.enemy_stats = enemy_stats
        self.interaction = interaction

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.danger)
    async def continue_button(self, interaction: discord.Interaction, button: Button):
        health_bar = generate_health_bar(self.user_entry["hp"])

        embed = discord.Embed(
            title=f"{interaction.user.display_name} vs **{self.enemy_name}**",
            description=f"{interaction.user.display_name} won't go down!",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=self.enemy_stats["image"])
        embed.add_field(name="Your stats:", value=f"**HP**: {self.user_entry['hp']} {health_bar}", inline=False)
        embed.add_field(
        name="",
        value=(
            f"**Strength**: {self.user_entry['strength']}  |  **Agility**: {self.user_entry['agility']}\n"
            f"**Endurance**: {self.user_entry['endurance']}  |  **Flexibility**: {self.user_entry['flexibility']}"
        ),
        inline=False
        )

        view = PlayerView(self.user_entry, self.enemy_name, self.enemy_stats, interaction)
        await interaction.message.edit(embed=embed, view=view)
        
        if not interaction.response.is_done():
            await interaction.response.defer()

class EnemyView(View):
    def __init__(self, user_entry, enemy_name, enemy_stats, interaction):
        super().__init__()
        self.user_entry = user_entry
        self.enemy_name = enemy_name
        self.enemy_stats = enemy_stats
        self.interaction = interaction

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.danger)
    async def continue_button(self, interaction: discord.Interaction, button: Button):
        evasionChance = 5 + (self.enemy_stats["precision"] - self.user_entry["flexibility"])
        evasionChance = max(5, min(50, evasionChance))

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
            embed.add_field(name=f"Your stats:", value=f"**HP**: {self.user_entry['hp']} {health_bar}", inline=False)
            embed.add_field(
            name="",
            value=(
                f"**Strength**: {self.user_entry['strength']}  |  **Agility**: {self.user_entry['agility']}\n"
                f"**Endurance**: {self.user_entry['endurance']}  |  **Flexibility**: {self.user_entry['flexibility']}"
            ),
            inline=False
            )

            view = PlayerView(self.user_entry, self.enemy_name, self.enemy_stats, self.interaction)
            await interaction.message.edit(embed=embed, view=view)
        else:
            baseDamage = self.enemy_stats["attack"]
            critical = False

            if random.randint(0, 100) <= 5:
                baseDamage = baseDamage * 2
                critical = True

            self.user_entry["hp"] -= baseDamage

            if self.user_entry["hp"] <= 0:
                reviveChance = max(20, self.user_entry["endurance"] / 10)

                randomRoll = random.randint(0, 100)

                if randomRoll <= reviveChance:
                    self.user_entry["hp"] += 1

                    embed = discord.Embed (
                        title=f"The **{self.enemy_name}** has attacked you!"
                    )
                    embed.set_thumbnail(url=self.enemy_stats["image"])
                    if critical:
                        embed.add_field(name="", value=f"**Critical hit!** You suffer {baseDamage} damage!", inline=False)
                    else:
                        embed.add_field(name="", value=f"You suffer {baseDamage} damage!", inline=False)
                    embed.add_field(name="", value=f"The **{self.enemy_name}** has knocked you down, but your muscles won't give up! You recover 1 HP!", inline=False)
                    view = ReviveView(self.user_entry, self.enemy_name, self.enemy_stats, self.interaction)
                    await interaction.message.edit(embed=embed, view=view)
                else:      
                    embed = discord.Embed (
                        title=f"The **{self.enemy_name}** has attacked you!"
                    )
                    embed.set_thumbnail(url=self.enemy_stats["image"])
                    if critical:
                        embed.add_field(name="", value=f"**Critical hit!** You suffer {baseDamage} damage!", inline=False)
                    else:
                        embed.add_field(name="", value=f"You suffer {baseDamage} damage!", inline=False)
                    embed.add_field(name="", value=f"You have fallen! The gym quickly calls an ambulance!", inline=False)
                    await interaction.message.edit(embed=embed, view=None)
            else:
                health_bar = generate_health_bar(self.user_entry["hp"])

                embed = discord.Embed(
                    title=f"{interaction.user.display_name} vs **{self.enemy_name}**",
                    description=f"",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=self.enemy_stats["image"])
                embed.add_field(name=f"The **{self.enemy_name}** has attacked you!", value=f"You suffer {baseDamage} damage!", inline=False)
                embed.add_field(name=f"Your stats:", value=f"**HP**: {self.user_entry['hp']} {health_bar}", inline=False)
                embed.add_field(
                name="",
                value=(
                    f"**Strength**: {self.user_entry['strength']}  |  **Agility**: {self.user_entry['agility']}\n"
                    f"**Endurance**: {self.user_entry['endurance']}  |  **Flexibility**: {self.user_entry['flexibility']}"
                ),
                inline=False
                )

                view = PlayerView(self.user_entry, self.enemy_name, self.enemy_stats, self.interaction)
                await interaction.message.edit(embed=embed, view=view)


        if not interaction.response.is_done():
            await interaction.response.defer()


class PlayerView(View):
    def __init__(self, user_entry, enemy_name, enemy_stats, interaction):
        super().__init__()
        self.user_entry = user_entry
        self.enemy_name = enemy_name
        self.enemy_stats = enemy_stats
        self.interaction = interaction

    @discord.ui.button(label="Punch", style=discord.ButtonStyle.danger)
    async def attack_button(self, interaction: discord.Interaction, button: Button):
        evasionChance = 5 + (self.user_entry["agility"] - self.enemy_stats["evasion"])
        evasionChance = max(5, min(50, evasionChance))

        randomRoll = random.randint(0, 100)

        if randomRoll <= evasionChance:
            embed = discord.Embed (
                title=f"The **{self.enemy_name}** dodged your punch!"
            )
            embed.set_thumbnail(url=self.enemy_stats["image"])
            embed.add_field(name="", value=f"It's the {self.enemy_name}'s turn!")
            view = EnemyView(self.user_entry, self.enemy_name, self.enemy_stats, self.interaction)
            await interaction.message.edit(embed=embed, view=view)
        else:
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
                        item_dropped = max(1, random.randint(value // 2, value))
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
                    title=f"You punch the **{self.enemy_name}**!"
                )
                embed.set_thumbnail(url=self.enemy_stats["image"])
                if critical:
                    embed.add_field(name="", value=f"**Critical hit!** You deal {baseDamage} damage!", inline=False)
                else:
                    embed.add_field(name="", value=f"You deal {baseDamage} damage!", inline=False)
                embed.add_field(name="", value=f"It's the {self.enemy_name}'s turn!", inline=False)
                view = EnemyView(self.user_entry, self.enemy_name, self.enemy_stats, self.interaction)
                await interaction.message.edit(embed=embed, view=view)

        if not interaction.response.is_done():
            await interaction.response.defer()

    @discord.ui.button(label="Skills", style=discord.ButtonStyle.primary)
    async def skills_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(f"You prepare a skill against the **{self.enemy_name}**!", ephemeral=True)

    @discord.ui.button(label="Inventory", style=discord.ButtonStyle.green)
    async def inventory_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("You check your inventory.", ephemeral=True)

    @discord.ui.button(label="Flee", style=discord.ButtonStyle.gray)
    async def flee_button(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title=f"{interaction.user.display_name}, you fled from the **{self.enemy_name}**!",
            description="",
            color=discord.Color.light_gray()
        )

        await interaction.message.edit(embed=embed, view=None)
        self.stop() 

@command(name='dungeon', description='Adventure inside a dungeon.')
async def dungeon(interaction, level: int):
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

    view = PlayerView(user_entry, enemy_name, enemy_stats, interaction)
    await interaction.response.send_message(embed=embed, view=view)

def setup(command_tree):
    command_tree.add_command(dungeon)
    dungeon.tree = command_tree