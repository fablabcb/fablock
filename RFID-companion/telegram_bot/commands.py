from typing import Literal
from telegram import BotCommand, BotCommandScopeChatAdministrators, Update
from telegram.ext import Application, ApplicationBuilder, ContextTypes, CommandHandler
import logging
import asyncio
import time
import telegram_bot.config as config
import queue

logger = logging.getLogger("telegram_bot")


# Returns `-1` on error or `None` if it should never expire.
# Otherwise, returns an integer representing the unix time.
def _parse_expiry(text: str) -> Literal[-1] | float | None:
    if text == "never":
        return None
    else:
        try:
            return time.mktime(time.strptime(text, "%Y-%m-%d"))
        except ValueError:
            return -1


class TelegramListener:
    application: Application
    rfid_command_queue: queue.SimpleQueue

    def __init__(self, rfid_command_queue: queue.SimpleQueue) -> None:
        self.rfid_command_queue = rfid_command_queue
        self.application = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()

    async def is_update_authorized(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        if update.effective_chat is None or update.effective_user is None:
            logger.error(
                "telegram update is missing important data (effective_chat or effective_user)"
            )
            return False

        if update.effective_chat.id != config.CHAT_ID:
            logger.warning(
                f"not authorized: {update.effective_chat.id=!r} {update.effective_chat.username=!r}"
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text="not authorized"
            )
            return False

        admins = await update.effective_chat.get_administrators()
        if not update.effective_user.id in [admin.user.id for admin in admins]:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text="not authorized, admins only"
            )
            return False

        return True

    async def start_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        assert update.effective_chat is not None

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=str(update.effective_chat.id)
        )

    async def create_card_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not await self.is_update_authorized(update, context):
            return

        assert update.effective_chat is not None and update.effective_user is not None

        if context.args is None or len(context.args) < 2:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="usage: /rfid_create <YYYY-MM-DD> <name>",
            )
            return

        expiry = _parse_expiry(context.args[0])
        if expiry == -1:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="invalid date format, use YYYY-MM-DD",
            )
            return

        self.rfid_command_queue.put("create")
        self.rfid_command_queue.put(expiry)
        self.rfid_command_queue.put(" ".join(context.args[1:]))

    async def cards_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not await self.is_update_authorized(update, context):
            return
        assert update.effective_chat is not None and update.effective_user is not None

        self.rfid_command_queue.put("list")

    async def expiry_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not await self.is_update_authorized(update, context):
            return
        assert update.effective_chat is not None and update.effective_user is not None

        if context.args is None or len(context.args) < 2:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="usage: /rfid_expiry <id> <YYYY-MM-DD>",
            )
            return

        # parse the card ID, it must be an integer
        id = None
        try:
            id = int(context.args[0], 10)
        except ValueError:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text="invalid id, must be an integer"
            )
            return

        expiry = _parse_expiry(context.args[1])
        if expiry == -1:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="invalid date format, use YYYY-MM-DD",
            )
            return

        self.rfid_command_queue.put("expiry")
        self.rfid_command_queue.put(id)
        self.rfid_command_queue.put(expiry)

    async def revoke_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not await self.is_update_authorized(update, context):
            return
        assert update.effective_chat is not None and update.effective_user is not None

        if context.args is None or len(context.args) < 1:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text="usage: /rfid_revoke <id>"
            )
            return

        # parse the card ID, it must be an integer
        id = None
        try:
            id = int(context.args[0], 10)
        except ValueError:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text="invalid id, must be an integer"
            )
            return

        self.rfid_command_queue.put("revoke")
        self.rfid_command_queue.put(id)

    async def toggle_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not await self.is_update_authorized(update, context):
            return
        assert update.effective_chat is not None and update.effective_user is not None

        self.rfid_command_queue.put("toggle")

    def listen(self) -> None:
        logger.info("setting up")

        self.application.add_handler(CommandHandler("start", self.start_callback))
        self.application.add_handler(CommandHandler("rfid_cards", self.cards_callback))
        self.application.add_handler(
            CommandHandler("rfid_create", self.create_card_callback)
        )
        self.application.add_handler(
            CommandHandler("rfid_expiry", self.expiry_callback)
        )
        self.application.add_handler(
            CommandHandler("rfid_revoke", self.revoke_callback)
        )
        self.application.add_handler(
            CommandHandler("rfid_toggle", self.toggle_callback)
        )

        asyncio.get_event_loop().run_until_complete(
            self.application.bot.set_my_commands(
                [
                    # /start is not documented because it is not intended to be used generally
                    # BotCommand('start', 'retrieve chat ID'),
                    BotCommand("rfid_cards", "list RFID cards"),
                    BotCommand("rfid_create", "create/write new RFID card"),
                    BotCommand("rfid_expiry", "set or remove expiry date of RFID card"),
                    BotCommand(
                        "rfid_revoke", "revoke and delete an existing RFID card"
                    ),
                    BotCommand("rfid_toggle", "enable/disable RFID reader"),
                ],
                BotCommandScopeChatAdministrators(config.CHAT_ID),
            )
        )

        logger.info("starting polling")
        self.application.run_polling()
