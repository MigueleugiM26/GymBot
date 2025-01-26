import discord
import json
import random
from commands.globalFunctions import load_user_data, load_xp_data, save_user_data, get_user_entry
from discord.app_commands import command
from discord import Interaction, Message
from discord.ui import Button, View
from functools import partial

with open("storage/groups.json", "r") as file:
    groups_data = json.load(file)


class ExerciseView(View):
    def __init__(self, exercises, user_entry):
        super().__init__()
        self.user_entry = user_entry
        self.exercises = exercises
        self.reps_done = {}
        
        for exercise in exercises:
            button = Button(label=exercise["name"], style=discord.ButtonStyle.primary, custom_id=exercise["name"])
            button.callback = partial(self.create_button_callback(exercise), button=button)
            self.add_item(button)

    def create_button_callback(self, exercise):
        async def button_callback(interaction: discord.Interaction, button: discord.ui.Button):
            exercise_name = exercise["name"]
            exercise_gif = exercise["gif"]
            reps = exercise["reps"]
            random_factor = random.randint(1, 3)
            total_reps = random_factor * reps
            self.reps_done[exercise_name] = 0  

            embed = discord.Embed(title=exercise_name, description="", color=discord.Color.dark_gold())
            embed.add_field(name="Repetitions (or seconds)", value=f"0/{total_reps}")
            embed.set_image(url=exercise_gif)

            btnMinusReps = Button(label="[-]", style=discord.ButtonStyle.red, disabled=True)
            btnPlusReps = Button(label="[+]", style=discord.ButtonStyle.green)
            btnFinish = Button(label="Finish Exercise", style=discord.ButtonStyle.primary, disabled=True)

            btnMinusReps.callback = partial(self.update_reps_callback, exercise_name=exercise_name, total_reps=total_reps, increment=False)
            btnPlusReps.callback = partial(self.update_reps_callback, exercise_name=exercise_name, total_reps=total_reps, increment=True)

            view = View()  
            view.add_item(btnMinusReps)  
            view.add_item(btnPlusReps)  
            view.add_item(btnFinish)  
            
            await interaction.response.send_message(
                embed=embed, 
                view=view
            )

            button.disabled = True
            await interaction.message.edit(view=self)

        return button_callback
    

    async def update_reps_callback(self, interaction: discord.Interaction, exercise_name: str, total_reps: int, increment: bool):
        exercise = next((ex for ex in self.exercises if ex["name"] == exercise_name), None)
    
        if exercise is None:
            return
    
        if increment:
            self.reps_done[exercise_name] += exercise["reps"]
        else:
            self.reps_done[exercise_name] -= exercise["reps"]

        current_reps = self.reps_done[exercise_name]

        embed = discord.Embed(title=exercise_name, description="", color=discord.Color.dark_gold())
        embed.add_field(name="Repetitions (or seconds)", value=f"{current_reps}/{total_reps}")
        embed.set_image(url=exercise["gif"])

        btnMinusReps = Button(label="[-]", style=discord.ButtonStyle.red, disabled=current_reps <= 0)
        btnPlusReps = Button(label="[+]", style=discord.ButtonStyle.green, disabled=current_reps >= total_reps)
        btnFinish = Button(label="Finish Exercise", style=discord.ButtonStyle.primary, disabled=current_reps < total_reps)

        btnMinusReps.callback = partial(self.update_reps_callback, exercise_name=exercise_name, total_reps=total_reps, increment=False)
        btnPlusReps.callback = partial(self.update_reps_callback, exercise_name=exercise_name, total_reps=total_reps, increment=True)
        btnFinish.callback = partial(self.finish_exercise_callback, exercise_name=exercise_name, button=btnFinish)

        view = View()
        view.add_item(btnMinusReps)
        view.add_item(btnPlusReps) 
        view.add_item(btnFinish)

        await interaction.response.edit_message(embed=embed, view=view)
    

    async def finish_exercise_callback(self, interaction: discord.Interaction, exercise_name: str, button: Button):
        exercise_stats = self.get_exercise_stats(exercise_name)
        button.disabled = True
        self.user_entry["exercisesDone"] += 1

        if self.user_entry["exercisesDone"] >= len(self.exercises): 
            embed = discord.Embed(title=f"Great job, {interaction.user.display_name}! You've completed {exercise_name}.\nYou have finished your exercises for today! Rest well! 💪", color=discord.Color.blurple())
        else:
            embed = discord.Embed(title=f"Great job, {interaction.user.display_name}! You've completed {exercise_name}. Keep going! 💪", color=discord.Color.blurple())

        embed.add_field(name="Skill", value=f"+1", inline=True)
        embed.add_field(name="Strength", value=f"+{exercise_stats["strength"]}", inline=True)
        embed.add_field(name="Agility", value=f"+{exercise_stats["agility"]}", inline=True)
        embed.add_field(name="Endurance", value=f"+{exercise_stats["endurance"]}", inline=True)
        embed.add_field(name="Flexibility", value=f"+{exercise_stats["flexibility"]}", inline=True)
        embed.add_field(name="", value="", inline=True)
        embed.set_image(url=None)
        await interaction.response.edit_message(
            embed=embed,
            view=None
        )

        await self.apply_exercise_stats(exercise_stats, interaction)

        user_data = load_user_data()
        user_id = str(interaction.user.id) 
        user_data[user_id] = self.user_entry  
        save_user_data(user_data)


    def get_exercise_stats(self, exercise_name):
        for exercise in self.exercises:
            if exercise["name"] == exercise_name:
                return {"strength": exercise["strength"], "agility": exercise["agility"], "endurance": exercise["endurance"], "flexibility": exercise["flexibility"]}
        return {"strength": 0, "agility": 0, "endurance": 0, "flexibility": 0}  


    async def apply_exercise_stats(self, stats, interaction):
        for stat, value in stats.items():
            if stat == "name": 
                break
            self.user_entry[stat] += value

        self.user_entry["skill"] += 1
        xp_data = load_xp_data()
        current_xp = self.user_entry["skill"]
        current_level = self.user_entry["level"]
        next_level_xp = xp_data.get(str(current_level + 1), None)

        if next_level_xp is None:
            return
        
        if current_xp >= next_level_xp:
            self.user_entry["level"] += 1
            self.user_entry["hp"] += 1

            embed = discord.Embed(title=f"Congratulations, {interaction.user.display_name}! You leveled up to level {self.user_entry['level']}!", color=discord.Color.red())
            embed.add_field(name="HP", value="+1", inline=True)

            await interaction.channel.send(
            embed=embed
            )

        if self.user_entry["level"] > len(xp_data):
            self.user_entry["level"] = len(xp_data)
            self.user_entry["hp"] -= 1
            

def get_random_exercise_set(interaction, groups_data, user_data):
    user_id = str(interaction.user.id)

    groupsDone = user_data[user_id]["groupsDone"]

    available_groups = [group for group in groups_data["groups"] if group["name"] not in groupsDone]

    if not available_groups:
        user_data[user_id]["groupsDone"] = []
        available_groups = groups_data["groups"]

    random_set = random.choice(available_groups)

    user_data[user_id]["groupsDone"].append(random_set["name"])

    return random_set


@command(name="workout", description="A set of exercises")
async def workout(interaction: Interaction):
    user_id = str(interaction.user.id) 
    get_user_entry(user_id)
    user_data = load_user_data() 
    user_entry = user_data.get(user_id)
    
    if user_entry["hasRoutine"]:
        if "workoutMessageId" in user_entry:
            try:
                workout_message = await interaction.channel.fetch_message(user_entry["workoutMessageId"])
                await interaction.response.send_message(
                    f"{interaction.user.display_name}, you already have an active routine today! Check it out here: {workout_message.jump_url}",
                    ephemeral=True
                )
                return
            except:
                pass 

        await interaction.response.send_message(
            f"{interaction.user.display_name}, you already have an active routine today!",
            ephemeral=True
        )

        return

    random_set = get_random_exercise_set(interaction, groups_data, user_data)
    exercises = random_set["exercises"]

    view = ExerciseView(exercises, user_entry)  
    exercises_list = "\n-".join([exercise["name"] for exercise in exercises])

    embed = discord.Embed(title=f"{interaction.user.display_name}, today, you will work out your **{random_set['name']}**!", color=discord.Color.dark_gold())
    embed.add_field(name="Exercises:", value=f"-{exercises_list}", inline=True)
    embed.set_footer(text="Click the buttons below for each exercise!")

    await interaction.response.defer()
    workout_message: Message = await interaction.followup.send(
        content=f"{interaction.user.mention}",  
        embed=embed,
        view=view
    )

    user_entry["hasRoutine"] = True
    user_entry["workoutMessageId"] = workout_message.id  
    user_data[user_id] = user_entry  
    save_user_data(user_data)


def setup(command_tree):
    command_tree.add_command(workout)
