from discord.app_commands import command

@command(name="ping", description="Latency.")
async def ping(interaction):
    bot_latency = round(ping.client.latency * 1000)
    await interaction.response.send_message(
        f"{bot_latency}ms")


def setup(command_tree):
    command_tree.add_command(ping)
    ping.client = command_tree.client
