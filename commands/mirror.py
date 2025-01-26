import discord
from discord.app_commands import command
from commands.globalFunctions import load_user_data, load_xp_data


@command(name='mirror', description='Look at yourself in the mirror.')
async def mirror(interaction):
    user_id = str(interaction.user.id)
    user_entry = load_user_data().get(user_id)

    if user_entry is None:
        await interaction.response.send_message(
            "You haven't gone to the gym yet.",
            ephemeral=True
        )
        return
    
    embed = discord.Embed(
        title=f"{interaction.user.display_name}, you look at yourself in the mirror.",
        description=f"Such a toned body, you feel happy about your progress.",
        color=discord.Color.blue()  
    )

    xp_data = load_xp_data()
    next_level_xp = xp_data.get(str(user_entry["level"] + 1), None)

    embed.add_field(name="Level", value=user_entry["level"], inline=True)
    if next_level_xp is None:
        embed.add_field(name="Skill", value=f"{user_entry["skill"]}", inline=True)
    else:
        embed.add_field(name="Skill", value=f"{user_entry["skill"]}/{next_level_xp}", inline=True)
    embed.add_field(name="HP", value=user_entry["hp"], inline=True)
    embed.add_field(name="Strength", value=user_entry["strength"], inline=True)
    embed.add_field(name="Agility", value=user_entry["agility"], inline=True)
    embed.add_field(name="Endurance", value=user_entry["endurance"], inline=True)
    embed.add_field(name="Flexibility", value=user_entry["flexibility"], inline=True)

    await interaction.response.send_message(embed=embed)


def setup(command_tree):
    command_tree.add_command(mirror)
    mirror.tree = command_tree
