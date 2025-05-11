import asyncio
import time
from threading import Thread
from flask import Flask
from pyrogram import idle
from pyrogram.filters import command, user

from bot import bot, Var, bot_loop, sch, LOGS
from bot.modules.up_posts import upcoming_animes

# Track bot start time
START_TIME = time.time()

# Format uptime into human-readable string
def get_uptime():
    seconds = int(time.time() - START_TIME)
    mins, secs = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)
    days, hrs = divmod(hrs, 24)
    uptime = f"{days}d {hrs}h {mins}m {secs}s" if days else f"{hrs}h {mins}m {secs}s"
    return uptime

# Basic /ping command with uptime
@bot.on_message(command('ping') & user(Var.ADMINS))
async def ping(client, message):
    uptime = get_uptime()
    await message.reply(f"<i>I'm alive and running!\nUptime: <b>{uptime}</b></i>")

# Flask webserver for health check
app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running!'

def run_flask():
    app.run(host='0.0.0.0', port=8000)

# Main bot function
async def main():
    await bot.start()
    LOGS.info('Minimal Auto Anime Bot started on Koyeb!')

    sch.add_job(upcoming_animes, "cron", hour=0, minute=30)
    sch.start()

    await idle()
    await bot.stop()
    LOGS.info('Bot stopped cleanly.')

if __name__ == '__main__':
    Thread(target=run_flask).start()  # Start Flask in a separate thread
    try:
        bot_loop.run_until_complete(main())
    except KeyboardInterrupt:
        LOGS.info('Bot manually stopped.')
