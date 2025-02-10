import os
from dotenv import load_dotenv
from datetime import datetime

# LLM Imports
import ollama

# Discord Imports
import discord
from discord.ext import commands


### Env Setup ###  
load_dotenv()

# Channels are defined in the .env file
allowed_channels = os.getenv('TESTING_CHANNELS')
BOT_TOKEN = os.getenv('PRODUCTION_TOKEN')




    ### Discord Setup ###  
# Setup Discord Permissions
intents = discord.Intents.default()

# Intents are defined both as permissions and in the code
# They are like events that the bot can listen to
intents.message_content = True

intents.typing = True
intents.presences = True
intents.members = True




##### Helper Functions #####
async def send_generated_image(message, prompt, file_path=None):
    # Create an embed
    embed = discord.Embed(
        title="Generated Image",
        description=f"Prompt: {prompt}",
        color=discord.Color.blue()
    )
    
    # Attach the image
    file = discord.File(f"images/{file_path}", filename=file_path)
    embed.set_image(url=f"attachment://{os.path.basename(file_path)}")

    # Send the embed with the image
    await message.channel.send(embed=embed, file=file)



async def get_chat_response(query):
    response = ollama.chat(model='2ndGraderAI', messages=[
        {
            'role': 'user',
            'content': query,
        },
    ])
    messageContent = response['message']['content']
    return messageContent


def parse_env_ids(env_variable):
    """Parse a comma-separated string of IDs from .env file and return a set of integers."""
    return {int(id.strip()) for id in os.getenv(env_variable, '').split(',') if id.strip()}


async def filter_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return False
    
    # Check if data type exists and is in expected form
    if isinstance(message.author, discord.Member):
        print(f"\tMessage Received From: {message.author.display_name}")
        # print(f"\tRoles: {[role.name for role in message.author.roles]}")  # List roles
    else:
        return False
    
    # Not an allowed channel
    if message.channel.id not in CHANNEL_IDS:
        print(f'Message not in allowed channels')
        return False
    
    # Passed All Cases
    return True

async def call_tool_llm(message):
    query = message.content
    tool_result = run_tool_prompt(query)
    print(f"Tool Result: {tool_result}")

    # Check if the result is an image file path
    if tool_result.endswith(('.png', '.jpg', '.jpeg', '.gif')):
        # Send the generated image
        file_path = tool_result
        print(f"\t> Sending a picture message: {file_path}")
        await send_generated_image(message, query, file_path)
    else:
        await message.channel.send(tool_result)



# Pick A Set Of Channels
CHANNEL_IDS = parse_env_ids('TESTING_CHANNELS')  
#CHANNEL_IDS = parse_env_ids('PRODUCTION_CHANNELS')

# Start the bot
bot = discord.Client(intents=intents)



    ##### Event Listeners #####  
# Define Callbacks for Intents Events
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    for channel_id in CHANNEL_IDS:
        channel = bot.get_channel(channel_id)
        if channel:
            print(f"Listening on Channel: {channel.name}")
        else:
            print(f"NOT LISTENING: Could not find channel with ID: {channel_id}")





@bot.event
async def on_message(message):
    # Did message pass all filters?
    good_message = await filter_message(message)
    
    # Skip if message fails tests
    if not good_message:
        return
    
    # Hello World - Ping Bot
    if message.content.startswith('$ping'):
        print('Hello World command received')
        return await message.channel.send(f'Hello, World! I\'m just chilling here with {message.author.display_name}!')

    
    # All Systems Go - Start Chat with LLM
    query = message.content
    response = await get_chat_response(query)
    await message.channel.send(response)
    
    
    # Tool Calling Instead
    # await call_tool_llm(message)




































@bot.event
async def on_typing(channel, user, when):
    print(f'{user} is typing in {channel} at {when}')

@bot.event
async def on_presence_update(before, after):
    # print(f'presenceUpdate: {before} | {after}:')
    
    # Print all attributes and methods of the before object
    # print(before.__dir__())
    
     # Print specific attributes
    # print(f'\tName: {before.name}')
    # print(f'\tStatus: {before.status}')
    
    print(f'> Login Log: {before.name} - {after.status} @{datetime.now().strftime("%H:%M")}')



##### Finally, run the bot #####
# bot.run(BOT_TOKEN)
bot.run('MTMzODU1ODY2ODc3MzI2MTM0NA.Gd1r6a.VEBHeL1DRTgTpmuHY7xEfUtqnPQbzPQQe7gpMk')