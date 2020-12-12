import asyncio
import logging
import threading
import multiprocessing
from construct import Container

from xbox.nano.render.client import Client
from xbox.nano.render.sink import Sink
from xbox.nano.render.video.sdl import SDLVideoRenderer
from xbox.nano.render.audio.sdl import SDLAudioRenderer


class BlockingClient(Client):
    def start_loop(self):
        self.loop()

    def loop(self):
        self._running = True
        while self._running:
            self.pump()


class PipedSink(Sink):
    def __init__(self, pipe):
        self.pipe = pipe

    def open(self, client):
        # Ignore client for now, only needed for input
        self.pipe.send('open')

    def close(self):
        self.pipe.send('close')

    def setup(self, fmt):
        self.pipe.send(fmt)

    def render(self, data):
        self.pipe.send(data)


async def protocol_runner(video_pipe, audio_pipe):
    from xbox.sg.console import Console
    from xbox.nano.manager import NanoManager
    from xbox.nano.render.client import Client

    logging.basicConfig(level=logging.DEBUG)

    consoles = await Console.discover(timeout=1)
    if len(consoles):
        console = consoles[0]

        console.add_manager(NanoManager)
        await console.connect()
        await console.wait(1)
        print('connected')
        await console.nano.start_stream()
        await console.wait(2)

        client = Client(PipedSink(video_pipe), PipedSink(audio_pipe), Sink())
        await console.nano.start_gamestream(client)
        print('stream started')
        try:
            while True:
                await asyncio.sleep(5.0)
        except KeyboardInterrupt:
            pass

    print('protocol_runner exit')


def sink_pump(pipe, sink):
    while True:
        data = pipe.recv()
        if isinstance(data, Container):
            sink.setup(data)
        elif data == 'open':
            # sink.open(None)
            pass
        elif data == 'close':
            sink.close()
        else:
            sink.render(data)


async def async_main():
    logging.basicConfig(level=logging.DEBUG)

    vparent, vchild = multiprocessing.Pipe()
    aparent, achild = multiprocessing.Pipe()
    protocol_proc = multiprocessing.Process(
        target=protocol_runner, args=(vchild, achild)
    )
    protocol_proc.start()

    client = BlockingClient(
        SDLVideoRenderer(1280, 720),
        SDLAudioRenderer(),
        Sink()
    )

    video_pumper = threading.Thread(
        target=sink_pump, args=(vparent, client.video)
    )
    video_pumper.start()

    audio_pumper = threading.Thread(
        target=sink_pump, args=(aparent, client.audio)
    )
    audio_pumper.start()

    client.open(None)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_main())


if __name__ == '__main__':
    main()
