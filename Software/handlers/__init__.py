import asyncio
import logging
import states


class Manager:
    handlers: list["Handler"]

    def __init__(self):
        self.handlers = []

    async def request_open(self, name: str, handler_name: str) -> bool:
        """
        Request opening by the given authorized person.

        Returns whether the request was successful.
        """
        try:
            await asyncio.gather(
                *[
                    handler.send(f"opening for {name} (via {handler_name})", critical=True)
                    for handler in self.handlers
                ],
                return_exceptions=True,
            )
        except RuntimeError:
            logging.error("unlocking failed because message could not be sent")
            return False  # don't unlock if this message could not be sent

        return states.unlock()

    async def broadcast(self, message: str):
        """
        Send a broadcast message to all channels.

        The message will be send using `Handler.send` on all available handlers.
        The message will be sent as a non-critical message.
        """
        await asyncio.gather(
            *[handler.send(message) for handler in self.handlers],
            return_exceptions=False,
        )

    async def run(self):
        await asyncio.gather(
            *[handler.listen(self) for handler in self.handlers],
            return_exceptions=True,
        )


class Handler:
    async def send(self, message: str, critical: bool = False):
        """
        Send a broadcast message to this channel.

        If the `critical` flag is set and sending the message fails, raise a `RuntimeError`.
        Otherwise, failure to send the message is silently ignored.

        The default implementation does nothing.
        """
        pass

    async def listen(self, manager: Manager):
        """
        Runs the event loop for this channel.

        If a message is received that is deemed acceptable, call `request_open`
        to perform the opening sequence, pass the name of the authorized user.
        The callback will return whether the request to open was successful.
        """
        raise NotImplementedError()
