import os
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp
import logging
from pytube import YouTube
import requests
import re

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('discord_bot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Set up the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# YouTube downloader options
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'opus',
        'preferredquality': '192',
    }],
}

# FFMPEG options for audio playback
ffmpeg_options = {
    'options': '-vn'
}

# Queue to store songs
song_queue = []

async def download_song(url):
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename.rsplit(".", 1)[0] + ".opus"
    except Exception as e:
        logger.error(f"Error downloading with yt-dlp: {str(e)}")
        try:
            yt = YouTube(url)
            stream = yt.streams.filter(only_audio=True).first()
            out_file = stream.download(output_path='downloads')
            return out_file
        except Exception as e:
            logger.error(f"Error downloading with pytube: {str(e)}")
            return None

async def play_song(voice_client, file_path):
    retries = 3
    for i in range(retries):
        try:
            logger.info(f"Attempting to play {file_path} (Attempt {i+1}/{retries})")
            source = discord.FFmpegOpusAudio(file_path, **ffmpeg_options)
            voice_client.play(source, after=lambda e: logger.info(f"Finished playing: {e}"))
            logger.info(f"Successfully started playing {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error playing song (Attempt {i+1}/{retries}): {str(e)}")
            await asyncio.sleep(1)
    return False

async def play_next(interaction):
    if song_queue:
        next_song = song_queue.pop(0)
        voice_client = interaction.guild.voice_client
        
        try:
            file_path = await download_song(next_song['url'])
            logger.info(f"Downloaded song to {file_path}")
            if file_path and os.path.exists(file_path):
                success = await play_song(voice_client, file_path)
                if success:
                    await interaction.followup.send(f"Now playing: {next_song['title']}")
                else:
                    await interaction.followup.send(f"Failed to play {next_song['title']} after multiple attempts.")
            else:
                await interaction.followup.send(f"Failed to download {next_song['title']}.")
        except Exception as e:
            logger.error(f"Error in play_next: {str(e)}")
            await interaction.followup.send(f"An error occurred while playing {next_song['title']}: {str(e)}")
        
        # Schedule next song
        bot.loop.create_task(check_queue(interaction))
    else:
        await interaction.followup.send("Queue is empty. Use /play to add more songs!")

async def check_queue(interaction):
    while True:
        await asyncio.sleep(5)  # Check every 5 seconds
        voice_client = interaction.guild.voice_client
        if voice_client and not voice_client.is_playing() and song_queue:
            await play_next(interaction)
        elif not song_queue:
            break

@bot.tree.command(name="play", description="Play a song")
@app_commands.describe(song="The URL or name of the song to play")
async def play(interaction: discord.Interaction, song: str):
    await interaction.response.defer()
    
    if not interaction.user.voice:
        await interaction.followup.send("You need to be in a voice channel to use this command!")
        return

    voice_channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client

    if not voice_client:
        voice_client = await voice_channel.connect()
    elif voice_client.channel != voice_channel:
        await voice_client.move_to(voice_channel)

    try:
        if not song.startswith('http'):
            search_url = f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}"
            html = requests.get(search_url).text
            video_ids = re.findall(r"watch\?v=(\S{11})", html)
            if video_ids:
                song = f"https://www.youtube.com/watch?v={video_ids[0]}"
            else:
                await interaction.followup.send("No search results found.")
                return

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song, download=False)
            song_info = {
                'url': info['webpage_url'],
                'title': info['title']
            }

        if not voice_client.is_playing():
            song_queue.append(song_info)
            await play_next(interaction)
        else:
            song_queue.append(song_info)
            await interaction.followup.send(f"Added to queue: {song_info['title']}")
    except Exception as e:
        logger.error(f"Error in play command: {str(e)}")
        await interaction.followup.send(f"An error occurred: {str(e)}")

@bot.tree.command(name="skip", description="Skip the current song")
async def skip(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message("Skipped the current song.")
    else:
        await interaction.response.send_message("No song is currently playing.")

@bot.tree.command(name="queue", description="View the current queue")
async def queue(interaction: discord.Interaction):
    if not song_queue:
        await interaction.response.send_message("The queue is empty.")
    else:
        queue_list = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(song_queue)])
        await interaction.response.send_message(f"Current queue:\n{queue_list}")

@bot.tree.command(name="stop", description="Stop the bot")
async def stop(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client:
        voice_client.stop()
        await voice_client.disconnect()
        song_queue.clear()
        await interaction.response.send_message("Stopped playing and cleared the queue.")
    else:
        await interaction.response.send_message("The bot is not connected to a voice channel.")

@bot.tree.command(name="help", description="Help command")
async def help_command(interaction: discord.Interaction):
    help_text = (
        "🎶 Commands:\n"
        "/play: Play a song\n"
        "/skip: Skip the current song\n"
        "/queue: View the current queue\n"
        "/stop: Clears queue, stops music and leaves the channel\n"
        "/help: Help command\n"
        "/health: Health command"
    )
    await interaction.response.send_message(help_text, ephemeral=True)

@bot.tree.command(name="health", description="Health command")
async def health(interaction: discord.Interaction):
    await interaction.response.send_message("Bot is operational!", ephemeral=True)

@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Error syncing commands: {str(e)}")

# Run the bot
bot.run(TOKEN)