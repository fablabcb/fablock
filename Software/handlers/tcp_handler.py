import asyncio
import config
import logging
import socket
import ssl
from . import Handler, Manager


logger = logging.getLogger("tcp")

# TCP level keepalive is used for keeping the connection up.
#
# The client can request one of these actions.
RX_OPEN = 0x00
RX_BROADCAST = 0x01
# Followed by a UTF-8 encoded string.
# The end of the string is delimited by a byte that cannot occur in valid UTF-8.
RX_STRING_DELIM = bytes([0xFF])

# The server will respond with a zero byte if this operation was successful.
TX_ACK = 0x00
# Otherwise the server will respond with a 0x01 byte.
TX_NAK = 0x01


class TcpHandler(Handler):
    async def listen(self, manager: Manager):
        context = ssl.create_default_context(
            ssl.Purpose.CLIENT_AUTH, cafile=config.TLS_CLIENT_CERT_PATH
        )
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = (
            False  # checking the hostname on the self signed cert is not necessary
        )
        context.load_cert_chain(
            certfile=config.TLS_SERVER_CERT_PATH, keyfile=config.TLS_SERVER_KEY_PATH
        )

        lock = asyncio.Lock()

        def setup_connection(client_writer: asyncio.StreamWriter):
            # enable and configure TCP keepalive
            con: ssl.SSLSocket = client_writer.get_extra_info("socket")
            con.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            con.setsockopt(
                socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 15
            )  # idle seconds (15s)
            con.setsockopt(
                socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 15
            )  # seconds between keepalive (15s)
            con.setsockopt(
                socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 4
            )  # maximum number of keepalive fails to be acceptable (4 * 15s = 1min)

            addr = con.getpeername()
            logger.info("connection from " + repr(addr))

        async def client_handler(
            client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter
        ):
            try:
                if lock.locked():
                    # only one concurrent connection is allowed
                    return

                async with lock:
                    setup_connection(client_writer)

                    while True:
                        try:
                            # receive a packet (1 byte)
                            data = await client_reader.readexactly(1)
                        except Exception as e:
                            # some error during receiving, might have been a timeout
                            logger.error("error while receiving", exc_info=e)
                            break

                        assert len(data) == 1

                        if data[0] == RX_OPEN:
                            name = await client_reader.readuntil(RX_STRING_DELIM)
                            name = name.removesuffix(RX_STRING_DELIM).decode(
                                "utf-8", errors="replace"
                            )
                            logger.info("opening requested")
                            if await manager.request_open(name):
                                client_writer.write(bytes([TX_ACK]))
                            else:
                                client_writer.write(bytes([TX_NAK]))
                            await client_writer.drain()
                        elif data[0] == RX_BROADCAST:
                            message = await client_reader.readuntil(RX_STRING_DELIM)
                            message = message.removesuffix(RX_STRING_DELIM).decode(
                                "utf-8", errors="replace"
                            )
                            logger.info("broadcast message requested")
                            await manager.broadcast(message)
                        else:
                            logger.warning(
                                "closing connection due to unrecognized message: ",
                                repr(data),
                            )
                            break
                    logger.info("connection lost")
            except Exception as e:
                # it seems that asyncio server just discards the error
                logger.error("client handler failed", exc_info=e)

        await asyncio.start_server(
            client_handler,
            port=config.NETWORKING_PORT,
            ssl=context,
        )
