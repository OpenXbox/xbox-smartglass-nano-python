import sdl2
import logging
from xbox.nano.enum import AudioCodec
from xbox.nano.render.sink import Sink
from xbox.nano.render.codec import FrameDecoder
from xbox.nano.render.audio.aac import AACFrame, AACProfile, AACResampler

log = logging.getLogger(__name__)


class AudioRenderError(Exception):
    pass


class SDLAudioRenderer(Sink):
    def __init__(self, sample_size=4096):
        self._sample_size = sample_size
        self._sample_rate = None
        self._channels = None
        self._audio_spec = None
        self._decoder = None
        self._resampler = None
        self._dev = None
        self._fmt = None

    def open(self, client):
        sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_AUDIO)

    def close(self):
        sdl2.SDL_PauseAudioDevice(self._dev, 1)
        sdl2.SDL_CloseAudioDevice(self._dev)

    def setup(self, fmt):
        if fmt.codec == AudioCodec.AAC:
            sdl_audio_fmt = sdl2.AUDIO_F32LSB
            self._resampler = AACResampler(
                'flt', fmt.sample_rate, fmt.channels
            )
        elif fmt.codec == AudioCodec.PCM:
            raise TypeError("PCM format not implemented")
        elif fmt.codec == AudioCodec.Opus:
            raise TypeError("Opus format not implemented")
        else:
            raise TypeError("Unknown audio codec: %d" % fmt.codec)

        self._channels = fmt.channels
        self._sample_rate = fmt.sample_rate
        self._decoder = FrameDecoder.audio(fmt.codec)

        dummy_callback = sdl2.SDL_AudioCallback()

        target_spec = sdl2.SDL_AudioSpec(
            self._sample_rate, sdl_audio_fmt, self._channels,
            self._sample_size, dummy_callback
        )

        self._audio_spec = sdl2.SDL_AudioSpec(
            self._sample_rate, sdl_audio_fmt, self._channels,
            self._sample_size, dummy_callback
        )

        self._dev = sdl2.SDL_OpenAudioDevice(
            None, 0, target_spec, self._audio_spec,
            sdl2.SDL_AUDIO_ALLOW_FORMAT_CHANGE
        )

        if not self._dev:
            raise AudioRenderError(
                "SDL: Could not open audio device: %s - exiting",
                sdl2.SDL_GetError()
            )

        # TODO: Is this even possible?
        if target_spec.format != self._audio_spec.format:
            log.error("SDL: We didn't get requested audio format")

        # Start playback
        sdl2.SDL_PauseAudioDevice(self._dev, 0)

    def render(self, data):
        # TODO: Make decoder recognize data
        # without adding a header manually
        data = AACFrame.generate_header(
            len(data), AACProfile.Main,
            self._sample_rate, self._channels
        ) + data

        for frame in self._decoder.decode(data):
            if self._resampler:
                frame = self._resampler.resample(frame)
            audio_data = frame.planes[0].to_bytes()
            sdl2.SDL_QueueAudio(
                self._dev, audio_data, len(audio_data)
            )
