import logging
import asyncio
from json import loads as jloads
from aiohttp import ClientSession, ClientTimeout
from pyrogram.enums import ParseMode
from os import path as ospath

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

async def fetch_schedule_with_retry(max_retries=3):
    """Fetch schedule from API with proper content-type handling"""
    url = "https://subsplease.org/api/?f=schedule&h=true&tz=Asia/Kolkata"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json'
    }
    
    for attempt in range(max_retries):
        try:
            async with ClientSession(timeout=ClientTimeout(total=10)) as session:
                async with session.get(url, headers=headers) as response:
                    LOGS.info(f"Attempt {attempt+1}: Status {response.status}")
                    
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                        
                    content = await response.text()
                    
                    try:
                        data = jloads(content)
                        if not data or not isinstance(data.get('schedule'), list):
                            raise Exception("Invalid schedule data format")
                            
                        LOGS.info(f"Successfully parsed {len(data['schedule'])} shows")
                        return data
                        
                    except ValueError as e:
                        raise Exception(f"Invalid JSON: {str(e)}. Content: {content[:200]}...")
                    
        except Exception as e:
            LOGS.warning(f"Attempt {attempt+1} failed: {str(e)}")
            if attempt == max_retries - 1:
                LOGS.error("All retries exhausted")
                raise Exception(f"Failed after {max_retries} attempts: {str(e)}")
            await asyncio.sleep(2 ** attempt)


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
                
                entry = f"""
<b>🎬 {title}</b>
<blockquote>🕒 {anime['time']}  •  ⭐ {score}/100</blockquote>
"""
                anime_entries.append(entry)

            except Exception as e:
                LOGS.error(f"Error processing anime {anime['title']}: {str(e)}")
                continue

        total_anime = len(anime_entries)
        footer = f"""
<code>──────────────────────</code>
<b>🌠 {total_anime} releases today</b>
"""
        message_text = header + "\n".join(anime_entries) + footer

        # Send or update the message
        if TD_SCHR:
            try:
                LOGS.info("Editing existing schedule message")
                await TD_SCHR.edit_text(
                    message_text,
                    disable_web_page_preview=True,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                LOGS.warning(f"Failed to edit message: {str(e)}, sending new one")
                TD_SCHR = await bot.send_message(
                    Var.MAIN_CHANNEL,
                    message_text,
                    disable_web_page_preview=True,
                    parse_mode=ParseMode.HTML
                )
                await TD_SCHR.pin(disable_notification=True)
        else:
            LOGS.info("Posting new schedule message")
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
                    lines.insert(i + 2, f"    • **Status :** ✅ __Uploaded__\n    • **Link :** {link}")
                    break
            
            await TD_SCHR.edit_text("\n".join(lines))
            LOGS.info("Schedule updated successfully")
            
        except Exception as e:
            LOGS.error(f"Failed to update schedule: {str(e)}")
            raise