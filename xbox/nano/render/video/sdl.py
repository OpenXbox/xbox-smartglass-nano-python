import logging
import threading
from ctypes import cast, c_ubyte, POINTER

import sdl2
import sdl2.ext

from xbox.nano.enum import VideoCodec
from xbox.nano.render.sink import Sink
from xbox.nano.render.codec import FrameDecoder

log = logging.getLogger(__name__)


class VideoRenderError(Exception):
    pass


class SDLVideoRenderer(Sink):
    TITLE = 'Nano SDL'

    def __init__(self, width, height, fullscreen=False):
        self._window = None
        self._window_dimensions = (width, height)
        self._window_flags = sdl2.SDL_WINDOW_FULLSCREEN if fullscreen else 0
        self._renderer = None
        self._texture = None
        self._decoder = None
        self._fmt = None

        self._lock = threading.Lock()

    def open(self, client):
        sdl2.ext.init()
        self._window = sdl2.ext.Window(
            self.TITLE, self._window_dimensions,
            (sdl2.SDL_WINDOWPOS_UNDEFINED, sdl2.SDL_WINDOWPOS_UNDEFINED),
            sdl2.SDL_WINDOW_OPENGL | sdl2.SDL_WINDOW_RESIZABLE |
            self._window_flags
        )

        self._renderer = sdl2.ext.Renderer(
            self._window, -1, None,
            sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC
        )

        self._window.show()

    def close(self):
        sdl2.SDL_DestroyTexture(self._texture)
        del self._renderer
        del self._window
        sdl2.ext.quit()

    def setup(self, fmt):
        if fmt.codec == VideoCodec.H264:
            pixel_fmt = sdl2.SDL_PIXELFORMAT_YV12
        elif fmt.codec == VideoCodec.YUV:
            raise TypeError("YUV format not implemented")
        elif fmt.codec == VideoCodec.RGB:
            raise TypeError("RGB format not implemented")
        else:
            raise TypeError("Unknown video codec: %d" % fmt.codec)

        self._decoder = FrameDecoder.video(fmt.codec)
        self._texture = sdl2.SDL_CreateTexture(
            self._renderer.sdlrenderer, pixel_fmt,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            fmt.width, fmt.height
        )

    def render(self, data):
        renderer = self._renderer.sdlrenderer
        try:
            for frame in self._decoder.decode(data):
                self._lock.acquire()
                intp = POINTER(c_ubyte)
                sdl2.SDL_UpdateYUVTexture(
                    self._texture, None,
                    cast(frame.planes[0].buffer_ptr, intp), frame.planes[0].line_size,
                    cast(frame.planes[1].buffer_ptr, intp), frame.planes[1].line_size,
                    cast(frame.planes[2].buffer_ptr, intp), frame.planes[2].line_size,
                )
                self._lock.release()
                sdl2.SDL_RenderClear(renderer)
                sdl2.SDL_RenderCopy(renderer, self._texture, None, None)
                sdl2.SDL_RenderPresent(renderer)
        except Exception as e:
            log.debug('SDLVideoRenderer.render: {0}'.format(e))

    def pump(self):
        sdl2.SDL_PumpEvents()
        self._window.refresh()
