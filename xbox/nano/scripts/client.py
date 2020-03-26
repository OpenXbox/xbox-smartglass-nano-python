import sys
import logging
import argparse

from xbox.webapi.authentication.manager import AuthenticationManager

from xbox.sg.console import Console
from xbox.sg.enum import ConnectionState

from xbox.nano.manager import NanoManager
from xbox.nano.render.client import SDLClient
from xbox.nano.scripts import TOKENS_FILE


def main():
    parser = argparse.ArgumentParser(description="Basic smartglass client")
    parser.add_argument('--tokens', '-t', default=TOKENS_FILE,
                        help="Token file, created by xbox-authenticate script")
    parser.add_argument('--address', '-a',
                        help="IP address of console")
    parser.add_argument('--refresh', '-r', action='store_true',
                        help="Refresh xbox live tokens in provided token file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    try:
        auth_mgr = AuthenticationManager.from_file(args.tokens)
        auth_mgr.authenticate(do_refresh=args.refresh)
        auth_mgr.dump(args.tokens)
    except Exception as e:
        print("Failed to authenticate with provided tokens, Error: %s" % e)
        print("Please re-run xbox-authenticate to get a fresh set")
        sys.exit(1)

    userhash = auth_mgr.userinfo.userhash
    token = auth_mgr.xsts_token.jwt

    discovered = Console.discover(timeout=1, addr=args.address)
    if len(discovered):
        console = discovered[0]

        console.add_manager(NanoManager)
        console.connect(userhash, token)
        if console.connection_state != ConnectionState.Connected:
            print("Connection failed")
            sys.exit(1)

        console.wait(1)
        console.nano.start_stream()
        console.wait(2)

        client = SDLClient(1280, 720)
        console.nano.start_gamestream(client)

        try:
            console.protocol.serve_forever()
        except KeyboardInterrupt:
            pass
    else:
        print("No consoles discovered")
        sys.exit(1)


if __name__ == "__main__":
    main()
