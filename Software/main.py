import asyncio
import config
import hardware
from handlers import Manager, discourse_handler, telegram_handler, tcp_handler
import states


async def main():
    hardware.setup()

    manager = Manager()

    async def hardware_handler():
        state_machine = states.StateMachine(manager.broadcast)
        await state_machine.run()

    manager.handlers.append(telegram_handler.TelegramHandler())
    manager.handlers.append(discourse_handler.DiscourseHandler())

    if config.NETWORKING_ENABLED:
        manager.handlers.append(tcp_handler.TcpHandler())

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
