import asyncio
import config
import hardware
import handlers.telegram_handler, handlers.tcp_handler
import states


async def main():
    hardware.setup()

    manager = handlers.Manager()

    async def hardware_handler():
        state_machine = states.StateMachine(manager.broadcast)
        await state_machine.run()

    manager.handlers.append(handlers.telegram_handler.TelegramHandler())

    if config.NETWORKING_ENABLED:
        manager.handlers.append(handlers.tcp_handler.TcpHandler())

    await asyncio.gather(
        manager.run(),
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
