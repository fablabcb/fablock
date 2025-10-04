from collections.abc import Awaitable, Callable


class Handler:
    async def broadcast(self, message: str, critical: bool = False):
        """
        Send a broadcast message to this channel.

        If the `critical` flag is set and sending the message fails, raise a `RuntimeError`.
        Otherwise, failure to send the message is silently ignored.

        The default implementation does nothing.
        """
        pass

    async def listen(self, request_open: Callable[[str], Awaitable[bool]]):
        """
        Runs the event loop for this channel.

        If a message is received that is deemed acceptable, call `request_open`
        to perform the opening sequence, pass the name of the authorized user.
        The callback will return whether the request to open was successful.
        """
        raise NotImplementedError()
