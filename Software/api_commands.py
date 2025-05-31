import datetime
import logging
import requests
import secret_config
import states
import time
import uuid

OLD_MESSAGE_TIMEOUT = 30  # seconds


def send_message(text: str, critical=False):
    # (re)try up to 5 times if necessary
    for attempt in range(5):
        try:
            resp = requests.post(
                f"{secret_config.BASE_URL}/chat/{secret_config.CHAT_ID}",
                headers={
                    "api-key": secret_config.API_KEY,
                    "api-username": secret_config.API_USERNAME,
                },
                json={"message": text},
            )
            resp.raise_for_status()
            return
        except Exception as e:
            logging.warning(f"failed to send message, attempt={attempt}", exc_info=e)
            time.sleep(1)

    logging.error(f"failed to send message on final retry, critical={critical}")
    if critical:
        raise RuntimeError("failed to send message")


def check_badge(username: str) -> bool:
    resp = requests.get(
        f"{secret_config.BASE_URL}/user-badges/{username}.json",
        headers={
            "accept": "application/json",
            "api-key": secret_config.API_KEY,
            "api-username": secret_config.API_USERNAME,
        },
    )
    resp.raise_for_status()
    badge_ids = set(x["badge_id"] for x in resp.json()["user_badges"])
    return secret_config.REQUIRED_BADGE_ID in badge_ids


def listen() -> None:
    # when sending a last_message_id of -1, discourse will send a status
    # message stating the last id. As long as this last id isn't used, it'll
    # keep sending the status message and thus won't do long polling.
    last_message_id = -1

    client_id = uuid.uuid4().hex
    message_bus_channel = f"/chat/{secret_config.CHAT_ID}/new-message"

    while True:
        try:
            # discourse uses long polling by default
            resp = requests.post(
                f"{secret_config.BASE_URL}/message-bus/{client_id}/poll",
                headers={
                    "accept": "application/json",
                    "dont-chunk": "true",
                    "api-key": secret_config.API_KEY,
                    "api-username": secret_config.API_USERNAME,
                },
                json={
                    # which channels to subscribe to
                    message_bus_channel: last_message_id,
                },
            )
            if resp.status_code != 200:
                logging.warning(
                    f"message bus request returned status code {resp.status_code} (expected 200)"
                )
                time.sleep(10)
                continue
            data = resp.json()
        except Exception as err:
            logging.error("failed to poll message bus", exc_info=err)
            time.sleep(5)
            continue

        logging.debug("got message bus response: {data!r}")

        for message in data:
            if message["channel"] == "/__status":
                last_message_id = message["data"][message_bus_channel]
            elif message["channel"] == message_bus_channel:
                last_message_id = message["message_id"]

                content = message["data"]["message"]["message"]
                logging.debug(f"got new message: {content!r}")

                # check that message is not outdated
                message_created = datetime.datetime.fromisoformat(
                    message["data"]["message"]["created_at"]
                )
                now = datetime.datetime.now(message_created.tzinfo)
                if (now - message_created).total_seconds() > OLD_MESSAGE_TIMEOUT:
                    logging.warning("ignored outdated message")
                    continue

                # check that message is an open command
                if content != "/open":
                    continue

                username = message["data"]["message"]["user"]["username"]
                logging.info(f"got open request from user @{username}")

                # check that user is authorized
                if not check_badge(username):
                    send_message("not authorized")
                    continue

                try:
                    send_message(f"unlocking for @{username}", critical=True)
                except:
                    # sending the message failed, don't unlock
                    continue

                try:
                    states.leave_locked()
                except ValueError:
                    send_message("already busy")
