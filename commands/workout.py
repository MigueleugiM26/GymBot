import discord
from discord.app_commands import command
from discord import Interaction
from discord import Message
from discord.ui import Button, View
import json
import random
from functools import partial

with open("storage/groups.json", "r") as file:
    groups_data = json.load(file)

def load_user_data():
    with open("storage/users.json", "r") as file:
        return json.load(file)

def save_user_data(user_data):
    with open("storage/users.json", "w") as file:
        json.dump(user_data, file, indent=4)

def get_user_entry(user_id):
    user_data = load_user_data()
    user_id = str(user_id) 
    
    if user_id not in user_data:
        user_data[user_id] = {
            "level": 1, 
            "hp": 2,
            "strength": 1,
            "agility": 1,
            "endurance": 1,
            "flexibility": 1,
            "skill": 0,
            "hasRoutine": False,
            "hasWorkedOut": False,
            "workoutMessageId": ""
        }
        save_user_data(user_data)  
    return user_data[user_id]


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

            embed = discord.Embed(title=exercise_name, description="")
            embed.add_field(name="Repetitions", value=f"0/{total_reps}")
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
        if increment:
            self.reps_done[exercise_name] += self.exercises[0]["reps"]
        else:
            self.reps_done[exercise_name] -= self.exercises[0]["reps"]

        current_reps = self.reps_done[exercise_name]

        embed = discord.Embed(title=exercise_name, description="")
        embed.add_field(name="Repetitions", value=f"{current_reps}/{total_reps}")
        embed.set_image(url=self.exercises[0]["gif"])

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
        self.apply_exercise_stats(exercise_stats)
        button.disabled = True

        embed = discord.Embed(title=f"Great job! You've completed {exercise_name}. Keep going! 💪")
        embed.set_image(url=None)
        await interaction.response.edit_message(
            embed=embed,
            view=None
        )

        user_data = load_user_data()
        user_id = str(interaction.user.id) 
        user_data[user_id] = self.user_entry  
        save_user_data(user_data)


    def get_exercise_stats(self, exercise_name):
        for exercise in self.exercises:
            if exercise["name"] == exercise_name:
                return {"strength": exercise["strength"], "agility": exercise["agility"], "endurance": exercise["endurance"], "flexibility": exercise["flexibility"]}
        return {"strength": 0, "agility": 0, "endurance": 0, "flexibility": 0}  

    def apply_exercise_stats(self, stats):
        for stat, value in stats.items():
            if stat == "name": 
                break
            self.user_entry[stat] += value
            
        self.user_entry["skill"] += 1
        self.user_entry["level"] = int(1 + (self.user_entry["skill"] ** 1.2) / 10)

@command(name="workout", description="A set of exercises")
async def workout(interaction: Interaction):
    user_data = load_user_data() 
    user_id = str(interaction.user.id) 
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

    random_set = random.choice(groups_data["groups"])
    exercises = random_set["exercises"]

    view = ExerciseView(exercises, user_entry)  
    exercises_list = "\n-".join([exercise["name"] for exercise in exercises])

    await interaction.response.defer()
    workout_message: Message = await interaction.followup.send(
        f"{interaction.user.mention}, today, you will work out your **{random_set['name']}**!\n\nExercises:\n-{exercises_list}\n\nClick the buttons below for each exercise!",
        view=view
    )

    user_entry["hasRoutine"] = True
    user_entry["workoutMessageId"] = workout_message.id  
    user_data[user_id] = user_entry  
    save_user_data(user_data)



def setup(command_tree):
    command_tree.add_command(workout)
