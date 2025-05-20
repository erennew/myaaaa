import base64
import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot  # Assuming Bot is your Client instance
from bot.__init__ import Var  # Ensure that Var is imported to access ADMINS and other settings


# Helper function to encode string to Base64
async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string


# Helper function to extract message ID from forwarded message or URL
async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == Var.FILE_STORE:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = r"https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern, message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(Var.FILE_STORE):
                return msg_id
    return 0


# Command for Batch Processing
@Bot.on_message(filters.private & filters.user(Var.ADMINS) & filters.command('batch'))
async def batch(client: Client, message: Message):
    while True:
        try:
            first_message = await client.ask(
                text="<blockquote>Forward the First Message from DB Channel (with Quotes)..</blockquote>\n\n<blockquote>or Send the DB Channel Post Link</blockquote>",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except:
            return
        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        else:
            await first_message.reply(
                "<blockquote>❌ Error</blockquote>\n\n<blockquote>This forwarded post is not from the DB Channel or this link is not correct.</blockquote>",
                quote=True
            )
            continue

    while True:
        try:
            second_message = await client.ask(
                text="<blockquote>Forward the Last Message from DB Channel (with Quotes)..</blockquote>\n<blockquote>or Send the DB Channel Post Link</blockquote>",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except:
            return
        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        else:
            await second_message.reply(
                "<blockquote>❌ Error</blockquote>\n\n<blockquote>This forwarded post is not from the DB Channel or this link is not correct.</blockquote>",
                quote=True
            )
            continue

    string = f"get-{f_msg_id * abs(Var.FILE_STORE)}-{s_msg_id * abs(Var.FILE_STORE)}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]]
    )
    await second_message.reply_text(
        f"<b><blockquote>Here is your link</blockquote></b>\n\n<blockquote>{link}</blockquote>",
        quote=True,
        reply_markup=reply_markup
    )


# Command for Link Generation
@Bot.on_message(filters.private & filters.user(Var.ADMINS) & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    while True:
        try:
            channel_message = await client.ask(
                text="<blockquote>Forward Message from the DB Channel (with Quotes)..</blockquote>\n<blockquote>or Send the DB Channel Post Link</blockquote>",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except:
            return
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        else:
            await channel_message.reply(
                "<blockquote>❌ Error</blockquote>\n\n<blockquote>This forwarded post is not from the DB Channel or this link is not correct.</blockquote>",
                quote=True
            )
            continue

    base64_string = await encode(f"get-{msg_id * abs(Var.FILE_STORE)}")
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]]
    )
    await channel_message.reply_text(
        f"<b><blockquote>Here is your link</blockquote></b>\n\n<blockquote>{link}</blockquote>",
        quote=True,
        reply_markup=reply_markup
    )


# Example Pause Command (with your given structure)
@Bot.on_message(filters.private & filters.user(Var.ADMINS) & filters.command('pause'))
async def pause(client: Client, message: Message):
    await message.reply("🛑 The bot has been paused. Please wait for further updates.")
