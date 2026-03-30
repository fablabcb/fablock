from collections.abc import Awaitable, Callable
import asyncio
import logging
import time
from datetime import datetime, timezone
from telegram import Bot, BotCommand, BotCommandScopeChat, Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import secret_config
from . import Handler, Manager

OLD_MESSAGE_TIMEOUT_SEC = 30


logger = logging.getLogger("telegram_handler")


class TelegramHandler(Handler):
    bot: Bot

    def __init__(self) -> None:
        super().__init__()

        self.bot = Bot(secret_config.TELEGRAM_TOKEN)

    # wrapper around telegram API that incorporates retries
    # because in the past we have had problems with messages failing to send
    # and the exceptions messing up everything
    async def send(self, message: str, critical: bool = False):
        # (re)try up to 5 times if necessary
        for attempt in range(5):
            try:
                await self.bot.send_message(
                    chat_id=secret_config.TELEGRAM_CHAT_ID, text=message
                )
                return
            except Exception as e:
                logger.warning(f"failed to send message, attempt={attempt}", exc_info=e)
                time.sleep(1)

        logger.error(f"failed to send message on final retry, critical={critical}")
        if critical:
            raise RuntimeError("failed to send message")

    async def listen(self, manager: Manager):
        # separate thread needs separate event loop
        asyncio.set_event_loop(asyncio.new_event_loop())

        async def start_callback(
            update: Update, context: ContextTypes.DEFAULT_TYPE
        ) -> None:
            logger.info("callback for /start")
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=str(update.effective_chat.id)
            )

        async def open_handler(
            update: Update, context: ContextTypes.DEFAULT_TYPE
        ) -> None:
            logger.debug("callback for /open")

            # get the current time in the same time zone as the server's sent date
            now = datetime.now(update.effective_message.date.tzinfo)
            if (
                now - update.effective_message.date
            ).total_seconds() > OLD_MESSAGE_TIMEOUT_SEC:
                logger.warning("ignored outdated message")
                return
            if now >= datetime(2026, 7, 1, tzinfo=timezone.utc):
                await self.send("Telegram access is no longer available, switch to Discourse or another access method. Getting started with Discourse: <https://community.fablab-cottbus.de/t/7>")
                return
            else:
                await self.send("Telegram access ends 2026-06-30, switch to Discourse or another access method. Getting started with Discourse: <https://community.fablab-cottbus.de/t/7>")
                await asyncio.sleep(2)

            if update.effective_chat.id == secret_config.TELEGRAM_CHAT_ID:
                username = update.message.from_user.full_name
                if not await manager.request_open(username, "Telegram"):
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id, text="already busy"
                    )
            else:
                logger.warning("not authorized: " + update.effective_chat.username)
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id, text="not authorized"
                    )
                except:
                    pass  # don't care if this fails

        application = ApplicationBuilder().token(secret_config.TELEGRAM_TOKEN).build()
        application.add_handler(CommandHandler("start", start_callback))
        application.add_handler(CommandHandler("open", open_handler))

        await application.bot.set_my_commands(
            [
                # /start is not documented because it is not intended to be used generally
                # BotCommand('start', 'retrieve chat ID'),
                BotCommand("open", "open fablock"),
            ],
            BotCommandScopeChat(secret_config.TELEGRAM_CHAT_ID),
        )

        async with application:
            await application.updater.start_polling()
            await application.start()
