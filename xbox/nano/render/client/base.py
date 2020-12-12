import asyncio
from typing import Optional

from xbox.nano.enum import ChannelClass


class ClientError(Exception):
    pass


class Client(object):
    def __init__(self, video, audio, input):
        self.video = video
        self.audio = audio
        self.input = input
        self.protocol = None

        self._running = False
        self._loop_task: Optional[asyncio.Task] = None

    def open(self, protocol):
        self.protocol = protocol
        self.video.open(self)
        self.audio.open(self)
        self.input.open(self)

        self.start_loop()

    def close(self):
        self.video.close()
        self.audio.close()
        self.input.close()

    def start_loop(self):
        self._loop_task = asyncio.create_task(self.loop())

    async def loop(self):
        self._running = True
        while self._running:
            self.pump()
            await asyncio.sleep(0.1)

    def pump(self):
        self.video.pump()
        self.audio.pump()
        self.input.pump()

    def set_video_format(self, video_fmt):
        self.video.setup(video_fmt)

    def set_audio_format(self, audio_fmt):
        self.audio.setup(audio_fmt)

    def render_video(self, data):
        self.video.render(data)

    def render_audio(self, data):
        self.audio.render(data)

    def send_input(self, frame, timestamp_dt):
        input_channel = self.protocol.get_channel(ChannelClass.Input)
        if input_channel and input_channel.reference_timestamp:
            input_channel.send_frame(frame, timestamp_dt)

    def controller_added(self, controller_index):
        control_channel = self.protocol.get_channel(ChannelClass.Control)
        if control_channel:
            control_channel.controller_added(controller_index)

    def controller_removed(self, controller_index):
        control_channel = self.protocol.get_channel(ChannelClass.Control)
        if control_channel:
            control_channel.controller_removed(controller_index)
