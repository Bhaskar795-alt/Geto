import asyncio
import logging
from pyrogram import Client, idle
from config import Config

logging.basicConfig(level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s")
log = logging.getLogger("GETO")

app = Client("geto_bot",
    api_id=Config.API_ID, api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins"))


async def main():
    await app.start()
    me = await app.get_me()
    log.info(f"🌹 GETO BOT started as @{me.username} ({me.id})")
    await idle()
    await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
