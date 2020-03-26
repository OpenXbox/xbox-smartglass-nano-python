from xbox.nano.render.client.base import Client
from xbox.nano.render.video.sdl import SDLVideoRenderer
from xbox.nano.render.audio.sdl import SDLAudioRenderer
from xbox.nano.render.input.sdl import SDLInputHandler
from xbox.nano.render.input.sdl_keyboard import SDLKeyboardInputHandler


class SDLClient(Client):
    def __init__(self, width, height, use_keyboard=False):
        super(SDLClient, self).__init__(
            SDLVideoRenderer(width, height),
            SDLAudioRenderer(),
            SDLInputHandler() if not use_keyboard else SDLKeyboardInputHandler(),
        )
