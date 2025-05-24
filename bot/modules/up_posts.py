import logging
import asyncio
import random
from json import loads as jloads
from aiohttp import ClientSession, ClientTimeout
from pyrogram.enums import ParseMode
from textwrap import shorten
from bot import Var, bot, ffQueue
from bot.core.text_utils import TextEditor
from bot.core.reporter import rep

# Initialize logging
LOGS = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

TD_SCHR = None  # Global variable for schedule message

# Style configuration
NETWORK_TEXT = "<a href='https://t.me/OngoingCTW'>📡 CTW</a>"
ANIME_MEDIA_LINKS = [
    "https://t.me/c/1333766434/1254",
    "https://i.ibb.co/gMs2DG6C/x.jpg",
    "https://i.ibb.co/F4ytZfyG/x.jpg",
    "https://i.ibb.co/N6rTvZXG/x.jpg",
    "https://i.ibb.co/bjGvJ7fL/x.jpg",
    "https://i.ibb.co/pB8SMVfz/x.png",
    "https://i.ibb.co/pB8SMVfz/x.png"


]

async def fetch_schedule_with_retry(max_retries=3):
    """Fetch schedule from API"""
    url = "https://subsplease.org/api/?f=schedule&h=true&tz=Asia/Kolkata"
    headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
    
    for attempt in range(max_retries):
        try:
            async with ClientSession(timeout=ClientTimeout(total=10)) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                    data = jloads(await response.text())
                    if not data or not isinstance(data.get('schedule'), list):
                        raise Exception("Invalid schedule data format")
                    return data
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"Failed after {max_retries} attempts: {str(e)}")
            await asyncio.sleep(2 ** attempt)

def get_current_style():
    """Returns a consistent style for the entire post"""
    styles = [
        # 1. Modern Card Style
        lambda title, time, score: f"""
🟢 <b>{title}</b>
⏳ <code>{time}</code> | ⭐ <code>{score}/10</code>
━━━━━━━━━━━━""",

        # 2. Bubble Chat Style
        lambda title, time, score: f"""
💬 <b>{title.upper()}</b>
🕒 <code>{time}</code> | 💯 <code>{score}%</code>
──────────────────""",

        # 3. Minimalist Divider
        lambda title, time, score: f"""
<b>┌ {title}</b>
<code>├ {time}
└ ★ {score}</code>""",

        # 4. App Notification Style
        lambda title, time, score: f"""
📱 <b>{title}</b>
<code>🕓 {time}  |  🔥 {score} Rating</code>
──────────────────""",

        # 6. Compact List Style
        lambda title, time, score: f"""
<b>• {title[:24]}...</b>
<code>  🕑 {time}  |  ⭐ {score}</code>""",

        # 7. Highlight Badge Style
        lambda title, time, score: f"""
<b>🟣 {title}</b>
<code>   ⏱️ {time}  |  🏆 {score} pts</code>
──────────────""",

        # 8. Dual Column Layout
        lambda title, time, score: f"""
<b>┏ Title: {title}</b>
<code>┣ Time: {time}
┗ Score: {score}/100</code>""",

        # 9. Social Media Style
        lambda title, time, score: f"""
📌 <b>{title}</b>
<code>⏰ {time}  •  👍 {score}%</code>
──────────────────""",

        # 10. Premium Glassmorphism
        lambda title, time, score: f"""
<b>◈ {title}</b>
<code>  ✦ {time}  ✦ {score}%</code>
══════════════""",

        # 11. iOS Notification
        lambda title, time, score: f"""
📲 <b>{title}</b>
<code>   {time}  •  ⭐️ {score}</code>
──────────────────""",

        # 12. Android Toast
        lambda title, time, score: f"""
<b>🟢 {title}</b>
<code>   🕓 {time}  ◈ {score}</code>
──────────────""",

        # 13. Dark Mode Optimized
        lambda title, time, score: f"""
<b>🌙 {title}</b>
<code>   ⏳ {time}  ✨ {score}</code>
──────────────────""",

        # 14. Compact Card
        lambda title, time, score: f"""
<b>▍ {title}</b>
<code>  {time}  ▎ {score}/10</code>""",

        # 15. Modern Dashboard
        lambda title, time, score: f"""
<b>▸ {title}</b>
<code>   {time}  •  {score}%</code>
──────────────────"""
    ]
    return random.choice(styles)

async def upcoming_animes():
    """Post today's anime schedule with clean formatting"""
    global TD_SCHR
    
    if not Var.SEND_SCHEDULE:
        LOGS.info("Schedule posting is disabled in config")
        return

    try:
        LOGS.info("Starting schedule update...")
        schedule = await fetch_schedule_with_retry()
        
        if not schedule or 'schedule' not in schedule:
            LOGS.error("Invalid schedule data received")
            raise Exception("Invalid schedule data")

        # Select one random style for entire post
        current_style = get_current_style()

        # Prepare the message
        header = """
<b>🌸 𝗔𝗡𝗜𝗠𝗘 𝗦𝗖𝗛𝗘𝗗𝗨𝗟𝗘 🌸</b>
<code>──────────────────────</code>
<b>📅 Today's Releases • IST</b>
<code>──────────────────────</code>
"""
        anime_entries = []
        
        for anime in schedule["schedule"][:15]:  # Limit to 15 anime
            try:
                editor = TextEditor(anime["title"])
                await editor.load_anilist()
                data = editor.adata
                title = data.get('title', {}).get('english') or anime['title']
                score = data.get('averageScore', 'N/A')
                
                anime_entries.append(current_style(
                    title, anime['time'], score
                ))

            except Exception as e:
                LOGS.error(f"Error processing anime {anime['title']}: {str(e)}")
                continue

        total_anime = len(anime_entries)
        footer = f"""
<code>──────────────────────</code>
<b>🌠 {total_anime} releases today</b>
{NETWORK_TEXT}
"""
        message_text = header + "\n".join(anime_entries) + footer

        # Send with media or text
        if ANIME_MEDIA_LINKS:
            media_url = random.choice(ANIME_MEDIA_LINKS)
            try:
                if media_url.lower().endswith('.gif'):
                    TD_SCHR = await bot.send_animation(
                        chat_id=Var.MAIN_CHANNEL,
                        animation=media_url,
                        caption=message_text,
                        parse_mode=ParseMode.HTML
                    )
                else:
                    TD_SCHR = await bot.send_photo(
                        chat_id=Var.MAIN_CHANNEL,
                        photo=media_url,
                        caption=message_text,
                        parse_mode=ParseMode.HTML
                    )
                await TD_SCHR.pin(disable_notification=True)
                return
            except Exception as e:
                LOGS.error(f"Media failed: {str(e)}")

        # Text fallback
        if TD_SCHR:
            try:
                await TD_SCHR.edit_text(
                    message_text,
                    disable_web_page_preview=True,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                TD_SCHR = await bot.send_message(
                    Var.MAIN_CHANNEL,
                    message_text,
                    disable_web_page_preview=True,
                    parse_mode=ParseMode.HTML
                )
        else:
            TD_SCHR = await bot.send_message(
                Var.MAIN_CHANNEL,
                message_text,
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML
            )
        await TD_SCHR.pin(disable_notification=True)

        LOGS.info("Schedule update completed successfully")

    except Exception as e:
        error_msg = f"⚠️ Schedule Error: {str(e)[:200]}"
        LOGS.exception("Failed to post schedule")
        await rep.report(error_msg, "error")
        raise

async def update_shdr(name, link):
    """Update schedule when an anime is uploaded"""
    global TD_SCHR
    if TD_SCHR:
        try:
            LOGS.info(f"Updating schedule for {name}")
            lines = TD_SCHR.text.split('\n')
            
            for i, line in enumerate(lines):
                if name in line:
                    lines.insert(i + 2, f"    • <b>Status:</b> ✅ Uploaded\n    • <b>Link:</b> {link}")
                    break
            
            await TD_SCHR.edit_text("\n".join(lines))
            LOGS.info("Schedule updated successfully")
            
        except Exception as e:
            LOGS.error(f"Failed to update schedule: {str(e)}")
            raises
