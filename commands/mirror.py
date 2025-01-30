import discord
import aiohttp
from discord.app_commands import command
from commands.globalFunctions import load_user_data, load_xp_data
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io


@command(name="mirror", description="Look at yourself in the mirror.")
async def mirror(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_entry = load_user_data().get(user_id)

    if user_entry is None:
        await interaction.response.send_message(
            "You haven't gone to the gym yet.",
            ephemeral=True
        )
        return

    xp_data = load_xp_data()
    current_level_xp = xp_data.get(str(user_entry["level"]), 0)
    next_level_xp = xp_data.get(str(user_entry["level"] + 1), None)

    current_xp = user_entry["skill"]
    if next_level_xp is not None and next_level_xp > current_level_xp:
        progress = (current_xp - current_level_xp) / (next_level_xp - current_level_xp)
        progress = max(0, min(1, progress))  
    else:
        progress = 1

    avatar_url = interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url

    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as response:
            avatar_bytes = await response.read()

    image_width, image_height = 420, 620 
    border_thickness = 10
    avatar_size = 120
    avatar_x = (image_width - avatar_size) // 2 
    avatar_y = 70 

    base_color = (25, 30, 40, 255)  
    gradient_color = (45, 50, 60, 255)  
    image = Image.new("RGBA", (image_width, image_height), base_color)
    draw = ImageDraw.Draw(image)

    for y in range(image_height):
        blend = y / image_height
        blended_color = tuple(
            int(base_color[i] * (1 - blend) + gradient_color[i] * blend) for i in range(4)
        )
        draw.line([(0, y), (image_width, y)], fill=blended_color)

    try:
        font_large = ImageFont.truetype("arial.ttf", 28)
        font_small = ImageFont.truetype("arial.ttf", 22)
        font_smaller = ImageFont.truetype("arial.ttf", 16)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_smaller = ImageFont.load_default()

    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((avatar_size, avatar_size))
    mask = Image.new("L", (avatar_size, avatar_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
    avatar.putalpha(mask)

    image.paste(avatar, (avatar_x, avatar_y), avatar)

    draw.text((image_width // 2, avatar_y + avatar_size + 25), f"{interaction.user.display_name}", font=font_large, fill=(255, 255, 255), anchor="mm")

    start_y = avatar_y + avatar_size + 65
    spacing = 40  

    draw.text((image_width // 2, start_y), f"Level: {user_entry['level']}", font=font_small, fill=(255, 255, 255), anchor="mm")
    draw.text((image_width // 2, start_y + spacing), f"HP: {user_entry['hp']}", font=font_small, fill=(255, 255, 255), anchor="mm")

    draw.text((image_width // 3 - 15, start_y + 2 * spacing), f"Strength: {user_entry['strength']}", font=font_small, fill=(255, 255, 255), anchor="mm")
    draw.text((2 * image_width // 3 + 15, start_y + 2 * spacing), f"Agility: {user_entry['agility']}", font=font_small, fill=(255, 255, 255), anchor="mm")

    draw.text((image_width // 3 - 15, start_y + 3 * spacing), f"Endurance: {user_entry['endurance']}", font=font_small, fill=(255, 255, 255), anchor="mm")
    draw.text((2 * image_width // 3 + 15, start_y + 3 * spacing), f"Flexibility: {user_entry['flexibility']}", font=font_small, fill=(255, 255, 255), anchor="mm")

    bar_width, bar_height = 300, 30
    bar_x, bar_y = (image_width - bar_width) // 2, start_y + 5 * spacing
    corner_radius = bar_height // 2     
    bar_fill = int(bar_width * progress)


    if bar_fill > 0:
            draw.rounded_rectangle(
                [bar_x, bar_y, bar_x + bar_fill, bar_y + bar_height], 
                fill=(59, 22, 22), 
                radius=corner_radius
            )
    draw.rounded_rectangle(
        [bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], 
        fill=None,
        outline=(200, 200, 200), 
        width=2, 
        radius=corner_radius
    )

    xp_text = f"{current_xp} {f'/ {next_level_xp}' if next_level_xp else ''}"
    draw.text((image_width // 2, bar_y + bar_height // 2), xp_text, font=font_small, fill=(255, 255, 255), anchor="mm")

    draw.text((bar_x - 10, bar_y + bar_height // 2), str(current_level_xp), font=font_smaller, fill=(255, 255, 255), anchor="rm")
    draw.text((bar_x + bar_width + 10, bar_y + bar_height // 2), str(next_level_xp) if next_level_xp else "∞", font=font_smaller, fill=(255, 255, 255), anchor="lm")

    draw.text((image_width // 2, bar_y + 45), "Skill", font=font_smaller, fill=(255, 255, 255), anchor="mm")


    border_color = (180, 180, 180, 255)
    draw.rectangle([(border_thickness // 2, border_thickness // 2), 
                    (image_width - border_thickness // 2, image_height - border_thickness // 2)], 
                   outline=border_color, width=border_thickness)

    # Reflections
    reflection_overlay = Image.new("RGBA", (image_width, image_height), (0, 0, 0, 0))
    reflection_draw = ImageDraw.Draw(reflection_overlay)

    reflection_color = (255, 255, 255, 80)  
    line_width = 3  

    reflection_draw.line([(400, 20), (340, 100)], fill=reflection_color, width=line_width)
    reflection_draw.line([(390, 20), (320, 110)], fill=reflection_color, width=line_width)

    reflection_draw.line([(20, 600), (80, 520)], fill=reflection_color, width=line_width)  
    reflection_draw.line([(30, 600), (100, 510)], fill=reflection_color, width=line_width) 

    reflection_overlay = reflection_overlay.filter(ImageFilter.GaussianBlur(2))

    image = Image.alpha_composite(image, reflection_overlay)
    
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="PNG")
    image_bytes.seek(0)

    file = discord.File(image_bytes, filename="mirror.png")
    await interaction.response.send_message(file=file)


def setup(command_tree):
    command_tree.add_command(mirror)
    mirror.tree = command_tree
