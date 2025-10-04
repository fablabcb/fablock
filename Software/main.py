import asyncio
import config
import hardware
import handlers.telegram_handler, handlers.tcp_handler
import logging
import states

async def main():
    hardware.setup()

    ingress_handlers: list[handlers.Handler] = [
        handlers.telegram_handler.TelegramHandler()
    ]

    async def request_open(name: str) -> bool:
        try:
            await asyncio.gather(
                *[
                    handler.broadcast(f"opening for {name}", critical=True)
                    for handler in ingress_handlers
                ],
                return_exceptions=True,
            )
        except RuntimeError:
            logging.error("unlocking failed because message could not be sent")
            return False  # don't unlock if this message could not be sent

        return states.unlock()

    async def hardware_handler():
        async def broadcast(message: str):
            await asyncio.gather(
                *[handler.broadcast(message) for handler in ingress_handlers],
                return_exceptions=False,
            )

        state_machine = states.StateMachine(broadcast)
        await state_machine.run()

    if config.NETWORKING_ENABLED:
        ingress_handlers.append(handlers.tcp_handler.TcpHandler())

    await asyncio.gather(
        *[handler.listen(request_open) for handler in ingress_handlers],
        hardware_handler(),
        return_exceptions=True,
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCtrl-C pressed.  Stopping PIGPIO and exiting...")
    finally:
        hardware.stop()
