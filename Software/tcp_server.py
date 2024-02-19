import socket
import ssl
import states
import logging

logger = logging.getLogger("tcp")

# TCP level keepalive is used for keeping the connection up.
#
# All packets are one byte in length.
# The client can request opening by sending a zero byte.
RX_OPEN = 0x00
# The server will respond with a zero byte if this operation was successful.
TX_ACK = 0x00
# Otherwise the server will respond with a 0x01 byte.
TX_NAK = 0x01

def connection_lost():
    logger.warning("connection lost")
    # TODO: send telegram message?

def run():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile=config.CLIENT_CERT_PATH)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = False # checking the hostname on the self signed cert is not necessary
    context.load_cert_chain(certfile=config.SERVER_CERT_PATH, keyfile=config.SERVER_KEY_PATH)

    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
        s.bind((config.NETWORKING_HOST, config.NETWORKING_PORT))
        # only accept one connection at a time
        s.listen(0)

        while True:
            con, addr = s.accept()
            # enable and configure TCP keepalive
            con.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            con.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 15) # idle seconds (15s)
            con.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 15) # seconds between keepalive (15s)
            con.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 4) # maximum number of keepalive fails to be acceptable (4 * 15s = 1min)

            with context.wrap_socket(con, server_side=True) as con:
                logger.info("connection from " + repr(addr))

                while True:
                    try:
                        # receive a packet (1 byte)
                        data = con.recv(1)
                    except:
                        # some error during receiving, might have been a timeout
                        connection_lost()
                        break

                    if len(data) == 0:
                        connection_lost()
                        break

                    if data[0] == RX_OPEN:
                        logger.info("opening requested")
                        try:
                            states.leave_locked()
                            con.sendall(bytes([TX_ACK]))
                        except ValueError:
                            con.sendall(bytes([TX_NAK]))
                        except:
                            connection_lost()
                            break
                    else:
                        logger.warning("closing connection due to unrecognized message: ", repr(data))
                        break
