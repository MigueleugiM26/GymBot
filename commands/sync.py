from discord.app_commands import command


@command(name='sync', description='Sync commands.')
async def sync(interaction):
    if interaction.user.id == 450842915024142374:
        await sync.tree.sync()
        await interaction.response.send_message('Commands synchronized')
        print('Command tree synced.')
    else:
        await interaction.response.send_message('Only the great Miguelindo can use this command.')


'''
def setup(command_tree):
    command_tree.add_command(sync)
    sync.tree = command_tree
'''
