import sys
import logging
import argparse
import asyncio

from xbox.webapi.authentication.manager import AuthenticationManager

from xbox.sg.console import Console
from xbox.sg.enum import ConnectionState

from xbox.nano.manager import NanoManager
from xbox.nano.render.client import SDLClient


def on_gamestream_error(error_msg) -> None:
    print(f'!!! Gamestream error occured: {error_msg}')
    sys.exit(1)


async def async_main():
    parser = argparse.ArgumentParser(description="Basic smartglass NANO client")
    parser.add_argument('--address', '-a',
                        help="IP address of console")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    discovered = await Console.discover(timeout=1, addr=args.address)
    if len(discovered):
        console = discovered[0]

        console.add_manager(NanoManager)
        console.nano.on_gamestream_error += on_gamestream_error

        await console.connect("", "")
        if console.connection_state != ConnectionState.Connected:
            print("Connection failed")
            sys.exit(1)

        await console.wait(1)
        await console.nano.start_stream()
        await console.wait(2)

        client = SDLClient(1280, 720)
        await console.nano.start_gamestream(client)

        try:
            while True:
                await console.wait(5.0)
        except KeyboardInterrupt:
            pass
    else:
        print("No consoles discovered")
        sys.exit(1)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_main())


if __name__ == "__main__":
    main()
