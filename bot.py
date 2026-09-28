import asyncio
import logging
import os
from aiohttp import web
from pyrogram import Client, idle
from config import Config

logging.basicConfig(level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s")
log = logging.getLogger("GETO")

app = Client("geto_bot",
    api_id=Config.API_ID, api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins"))


async def health(request):
    return web.Response(text="🌹 GETO BOT is alive!")


async def start_web_server():
    web_app = web.Application()
    web_app.router.add_get("/", health)
    web_app.router.add_get("/health", health)
    runner = web.AppRunner(web_app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info(f"✅ Web server started on port {port}")


async def main():
    await app.start()
    me = await app.get_me()
    log.info(f"🌹 GETO BOT started as @{me.username} ({me.id})")
    await start_web_server()
    await idle()
    await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
