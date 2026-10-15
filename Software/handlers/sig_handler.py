import asyncio
import logging
import signal

import config
import states

from . import Handler, Manager

logger = logging.getLogger("os_signal")


def sig_handler():
    logger.info("received SIGUSR1")
    # bypasses ordinary unlocking procedure like e.g. sending messages
    # because if this backup is being used, the message sending might
    # be broken and would then block unlocking
    states.unlock()


class SigHandler(Handler):
    async def listen(self, manager: Manager):
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGUSR1, sig_handler)

        # ensure that the event loop keeps running
        while True:
            await asyncio.sleep(1000)
