import os
import logging

import sdl2
import sdl2.ext

from xbox.nano.render.input.base import InputHandler, InputError, \
    GamepadButton, GamepadButtonState, GamepadAxis

LOGGER = logging.getLogger(__name__)


SDL_BUTTON_MAP = {
    sdl2.SDLK_UP: GamepadButton.DPadUp,
    sdl2.SDLK_DOWN: GamepadButton.DPadDown,
    sdl2.SDLK_LEFT: GamepadButton.DPadLeft,
    sdl2.SDLK_RIGHT: GamepadButton.DPadRight,
    sdl2.SDLK_e: GamepadButton.Start,
    sdl2.SDLK_q: GamepadButton.Back,
    sdl2.SDLK_1: GamepadButton.LeftThumbstick,
    sdl2.SDLK_2: GamepadButton.RightThumbstick,
    sdl2.SDLK_3: GamepadButton.LeftShoulder,
    sdl2.SDLK_4: GamepadButton.RightShoulder,
    sdl2.SDLK_ESCAPE: GamepadButton.Guide,
    sdl2.SDLK_s: GamepadButton.A,
    sdl2.SDLK_d: GamepadButton.B,
    sdl2.SDLK_a: GamepadButton.X,
    sdl2.SDLK_w: GamepadButton.Y
}

SDL_STATE_MAP = {
    sdl2.SDL_KEYDOWN: GamepadButtonState.Pressed,
    sdl2.SDL_KEYUP: GamepadButtonState.Released
}

"""
SDL_AXIS_MAP = {
    sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT: GamepadAxis.LeftTrigger,
    sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT: GamepadAxis.RightTrigger,
    sdl2.SDL_CONTROLLER_AXIS_LEFTX: GamepadAxis.LeftThumbstick_X,
    sdl2.SDL_CONTROLLER_AXIS_LEFTY: GamepadAxis.LeftThumbstick_Y,
    sdl2.SDL_CONTROLLER_AXIS_RIGHTX: GamepadAxis.RightThumbstick_X,
    sdl2.SDL_CONTROLLER_AXIS_RIGHTY: GamepadAxis.LeftThumbstick_Y
}
"""


class SDLKeyboardInputHandler(InputHandler):
    def __init__(self):
        self._open = False
        super(SDLKeyboardInputHandler, self).__init__()

    def open(self, client):
        super(SDLKeyboardInputHandler, self).open(client)

    def _open_controller(self):
        self._open = True
        controller_index = 0
        LOGGER.debug('Opening keyboard as controller {}'.format(controller_index))
        self.client.controller_added(controller_index)

    def pump(self):
        for event in sdl2.ext.get_events():
            if event.type == sdl2.SDL_KEYDOWN:
                if not self._open:
                    self._open_controller()

                button = event.key.keysym.sym
                gamepad_button = SDL_BUTTON_MAP.get(button, None)
                if not gamepad_button:
                    LOGGER.debug('Input key {} not supported'.format(button))
                    break

                self.set_button(
                    gamepad_button, GamepadButtonState.Pressed
                )

            elif event.type == sdl2.SDL_KEYUP:
                button = event.key.keysym.sym
                gamepad_button = SDL_BUTTON_MAP.get(button, None)
                if not gamepad_button:
                    LOGGER.debug('Input key {} not supported'.format(button))
                    break

                self.set_button(
                    gamepad_button, GamepadButtonState.Released
                )

            """
            elif event.type == sdl2.SDL_CONTROLLERAXISMOTION:
                axis = event.caxis.axis
                value = event.caxis.value
                self.set_axis(SDL_AXIS_MAP[axis], value)
            """
