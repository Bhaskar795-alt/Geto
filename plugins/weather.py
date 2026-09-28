import aiohttp
from pyrogram import Client, filters


@Client.on_message(filters.command("weather"))
async def weather_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /weather <city>")
    city = " ".join(message.command[1:])
    url = f"https://wttr.in/{city}?format=3"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            txt = await r.text()
    await message.reply_text(f"🌤️ {txt}")
