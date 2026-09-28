import asyncio
import logging
import os

from aiohttp import web
from pyrogram import Client, idle

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s"
)

log = logging.getLogger("GETO")


async def health(request):
    return web.Response(text="🌹 GETO BOT IS ALIVE!")


async def start_web():
    app_web = web.Application()
    app_web.router.add_get("/", health)
    app_web.router.add_get("/health", health)

    runner = web.AppRunner(app_web)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )

    await site.start()

    log.info(f"✅ Web server started on port {port}")


async def main():

    # IMPORTANT:
    # Client MUST be created inside this event loop.
    app = Client(
        "geto_bot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        plugins=dict(root="plugins")
    )

    try:
        await app.start()

        me = await app.get_me()

        log.info(
            f"🌹 GETO BOT started as @{me.username} ({me.id})"
        )

        await start_web()

        await idle()

    except Exception:
        log.exception("❌ GETO BOT crashed")

    finally:
        try:
            if app.is_connected:
                await app.stop()
        except Exception:
            log.exception("❌ Error while stopping bot")


if __name__ == "__main__":
    asyncio.run(main())
