import asyncio
from pyrogram import idle
from pyrogram.filters import command, user
from bot import bot, Var, bot_loop, sch, LOGS
from bot.modules.up_posts import upcoming_animes

@bot.on_message(command('ping') & user(Var.ADMINS))
async def ping(client, message):
    await message.reply("<i>I'm alive and running!</i>")

async def main():
    # Start the bot
    await bot.start()
    LOGS.info('Minimal Auto Anime Bot started on Koyeb!')

    # Add scheduler only if needed (optional)
    sch.add_job(upcoming_animes, "cron", hour=0, minute=30)
    sch.start()

    # Keep the bot running
    await idle()

    # Cleanup when stopping
    LOGS.info('Bot stopping...')
    await bot.stop()
    LOGS.info('Bot stopped cleanly.')

if __name__ == '__main__':
    try:
        bot_loop.run_until_complete(main())
    except KeyboardInterrupt:
        LOGS.info('Bot manually stopped.')
