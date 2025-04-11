#Core Imports
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
BOT_TOKEN = os.getenv('PRODUCTION_TOKEN')
ALLOWED_CHANNELS = {int(id.strip()) for id in os.getenv('PRODUCTION_CHANNELS', '').split(',') if id.strip()}



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
async def filter_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return False
    
    # Check if data type exists and is in expected form
    if isinstance(message.author, discord.Member):
        print(f"\tMessage Received From: {message.author.display_name}")
        print(f"\tRoles: {[role.name for role in message.author.roles]}")  # List roles
    else:
        return False
    
    # Not an allowed channel
    if message.channel.id not in ALLOWED_CHANNELS:
        print(f'Message not in allowed channels')
        return False
    
    # Passed All Cases
    return True



async def get_chat_response(query):
    response = ollama.chat(model='2ndGraderAI', messages=[
        {
            'role': 'user',
            'content': query,
        },
    ])
    messageContent = response['message']['content']
    return messageContent



##### Event Listeners #####  
# Start the bot
bot = discord.Client(intents=intents)

# Log on Login
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    for channel_id in ALLOWED_CHANNELS:
        channel = bot.get_channel(channel_id)
        if channel:
            print(f"Listening on Channel: {channel.name} ({channel_id})")
        else:
            print(f"NOT LISTENING: Could not find channel with ID: {channel_id}")


# Listen To Messages
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


##### Finally, run the bot #####
bot.run(BOT_TOKEN)