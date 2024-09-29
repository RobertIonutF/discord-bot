# Discord Music Bot

This Discord bot allows users to play music in voice channels using YouTube links or search queries.

## Features

- Play songs from YouTube links or search queries
- Queue system for multiple songs
- Skip current song
- View current queue
- Stop playback and clear queue
- Help command for quick reference

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your Discord bot token:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   ```
4. Run the bot:
   ```
   python bot.py
   ```

## Commands

- `/play <song>`: Play a song by providing a YouTube URL or search query
- `/skip`: Skip the current song
- `/queue`: View the current queue
- `/stop`: Stop playback, clear the queue, and disconnect the bot
- `/help`: Display available commands
- `/health`: Check if the bot is operational

## Usage

1. Invite the bot to your Discord server
2. Join a voice channel
3. Use the `/play` command with a YouTube link or search query to start playing music
4. Use other commands as needed to control playback and manage the queue

## Dependencies

- discord.py
- yt-dlp
- pytube
- python-dotenv
- requests

## Troubleshooting

If you encounter any issues:
1. Ensure all dependencies are correctly installed
2. Check that your Discord bot token is correctly set in the `.env` file
3. Make sure the bot has the necessary permissions in your Discord server
4. Review the console output for any error messages

For further assistance, please open an issue on the GitHub repository.
