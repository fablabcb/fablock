import asyncio
import datetime
import httpx
import logging
import secret_config
import uuid
from . import Handler, Manager

OLD_MESSAGE_TIMEOUT_SEC = 30

logger = logging.getLogger("discourse_handler")


class DiscourseHandler(Handler):
    client: httpx.AsyncClient

    def __init__(self) -> None:
        super().__init__()

        self.client = httpx.AsyncClient()

    async def send(self, message: str, critical: bool = False):
        # (re)try up to 5 times if necessary
        for attempt in range(5):
            try:
                resp = await self.client.post(
                    f"{secret_config.DISCOURSE_BASE_URL}/chat/{secret_config.DISCOURSE_CHAT_ID}",
                    headers={
                        "api-key": secret_config.DISCOURSE_API_KEY,
                        "api-username": secret_config.DISCOURSE_API_USERNAME,
                    },
                    json={"message": message},
                )
                resp.raise_for_status()
                return
            except Exception as e:
                logger.warning(f"failed to send message, {attempt=}", exc_info=e)
                await asyncio.sleep(1)

        logger.error(f"failed to send message on final retry, {critical=}")
        if critical:
            raise RuntimeError("failed to send message")

    async def listen(self, manager: Manager):
        # when sending a last_message_id of -1, discourse will send a status
        # message stating the last id. As long as this last id isn't used, it'll
        # keep sending the status message and thus won't do long polling.
        last_message_id = -1

        client_id = uuid.uuid4().hex
        message_bus_channel = f"/chat/{secret_config.DISCOURSE_CHAT_ID}/new-messages"

        while True:
            try:
                resp: httpx.Response = await self.client.post(
                    f"{secret_config.DISCOURSE_BASE_URL}/message-bus/{client_id}/poll",
                    headers={
                        "accept": "application/json",
                        "dont-chunk": "true",
                        "api-key": secret_config.DISCOURSE_API_KEY,
                        "api-username": secret_config.DISCOURSE_API_USERNAME,
                    },
                    json={
                        # which channels to subscribe to
                        message_bus_channel: last_message_id,
                    },
                    # discourse uses long polling by default
                    timeout=60.0,
                )
                if resp.status_code != 200:
                    logger.warning(
                        f"message bus request returned status code {resp.status_code} (expected 200)"
                    )
                    await asyncio.sleep(10)
                    continue
                data = resp.json()
            except Exception as err:
                logger.error("failed to poll message bus", exc_info=err)
                await asyncio.sleep(5)
                continue

            logger.debug(f"got message bus response: {data!r}")

            for message in data:
                if message["channel"] == "/__status":
                    last_message_id = message["data"][message_bus_channel]
                elif message["channel"] == message_bus_channel:
                    last_message_id = message["message_id"]

                    content = message["data"]["message"]["message"]
                    logger.debug(f"got new message: {content!r}")

                    # check that message is not outdated
                    message_created = datetime.datetime.fromisoformat(
                        message["data"]["message"]["created_at"]
                    )
                    now = datetime.datetime.now(message_created.tzinfo)
                    if (
                        now - message_created
                    ).total_seconds() > OLD_MESSAGE_TIMEOUT_SEC:
                        logger.warning("ignored outdated message")
                        continue

                    # check that message is an open command
                    if content != "/open":
                        continue

                    username = message["data"]["message"]["user"]["username"]
                    logger.info(f"got open request from user @{username}")

                    if not await manager.request_open(username):
                        await self.send("already busy")
