import os
import logging

import sdl2
import sdl2.ext

from xbox.nano.render.input.base import InputHandler, InputError, \
    GamepadButton, GamepadButtonState, GamepadAxis

log = logging.getLogger(__name__)


SDL_BUTTON_MAP = {
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP: GamepadButton.DPadUp,
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN: GamepadButton.DPadDown,
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT: GamepadButton.DPadLeft,
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT: GamepadButton.DPadRight,
    sdl2.SDL_CONTROLLER_BUTTON_START: GamepadButton.Start,
    sdl2.SDL_CONTROLLER_BUTTON_BACK: GamepadButton.Back,
    sdl2.SDL_CONTROLLER_BUTTON_LEFTSTICK: GamepadButton.LeftThumbstick,
    sdl2.SDL_CONTROLLER_BUTTON_RIGHTSTICK: GamepadButton.RightThumbstick,
    sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER: GamepadButton.LeftShoulder,
    sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER: GamepadButton.RightShoulder,
    sdl2.SDL_CONTROLLER_BUTTON_GUIDE: GamepadButton.Guide,
    sdl2.SDL_CONTROLLER_BUTTON_INVALID: GamepadButton.Unknown,
    sdl2.SDL_CONTROLLER_BUTTON_A: GamepadButton.A,
    sdl2.SDL_CONTROLLER_BUTTON_B: GamepadButton.B,
    sdl2.SDL_CONTROLLER_BUTTON_X: GamepadButton.X,
    sdl2.SDL_CONTROLLER_BUTTON_Y: GamepadButton.Y
}

SDL_AXIS_MAP = {
    sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT: GamepadAxis.LeftTrigger,
    sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT: GamepadAxis.RightTrigger,
    sdl2.SDL_CONTROLLER_AXIS_LEFTX: GamepadAxis.LeftThumbstick_X,
    sdl2.SDL_CONTROLLER_AXIS_LEFTY: GamepadAxis.LeftThumbstick_Y,
    sdl2.SDL_CONTROLLER_AXIS_RIGHTX: GamepadAxis.RightThumbstick_X,
    sdl2.SDL_CONTROLLER_AXIS_RIGHTY: GamepadAxis.RightThumbstick_Y
}

SDL_STATE_MAP = {
    sdl2.SDL_CONTROLLERBUTTONDOWN: GamepadButtonState.Pressed,
    sdl2.SDL_CONTROLLERBUTTONUP: GamepadButtonState.Released
}


class SDLInputHandler(InputHandler):
    def __init__(self):
        super(SDLInputHandler, self).__init__()

        sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_GAMECONTROLLER)
        ret = sdl2.SDL_GameControllerAddMappingsFromFile(
            os.path.join(
                os.path.dirname(__file__), 'controller_db.txt'
            ).encode('utf-8')
        )

        if ret == -1:
            raise InputError(
                "Failed to load GameControllerDB, %s", sdl2.SDL_GetError()
            )

    def open(self, client):
        super(SDLInputHandler, self).open(client)
        # Enumerate already plugged controllers
        for i in range(sdl2.SDL_NumJoysticks()):
            if sdl2.SDL_IsGameController(i):
                if sdl2.SDL_GameControllerOpen(i):
                    log.info("Opened controller: %i", i)
                    self.client.controller_added(i)
                else:
                    log.error("Unable to open controller: %i", i)
            else:
                log.error("Not a gamecontroller: %i", i)

    def pump(self):
        for event in sdl2.ext.get_events():
            if event.type == sdl2.SDL_CONTROLLERDEVICEADDED:
                controller = event.cdevice.which
                log.debug('Controller added: %i' % controller)
                self.controller_added(controller)
                sdl2.SDL_GameControllerOpen(event.cdevice.which)

            elif event.type == sdl2.SDL_CONTROLLERDEVICEREMOVED:
                controller = event.cdevice.which
                log.debug('Controller removed: %i' % controller)
                self.controller_removed(controller)
                # sdl2.SDL_GameControllerClose(event.cdevice.which)

            elif event.type == sdl2.SDL_CONTROLLERBUTTONDOWN:
                button = event.cbutton.button
                self.set_button(
                    SDL_BUTTON_MAP[button], GamepadButtonState.Pressed
                )

            elif event.type == sdl2.SDL_CONTROLLERBUTTONUP:
                button = event.cbutton.button
                self.set_button(
                    SDL_BUTTON_MAP[button], GamepadButtonState.Released
                )

            elif event.type == sdl2.SDL_CONTROLLERAXISMOTION:
                axis = event.caxis.axis
                value = event.caxis.value
                if axis in (sdl2.SDL_CONTROLLER_AXIS_LEFTY, sdl2.SDL_CONTROLLER_AXIS_RIGHTY):
                    value = -value
                if axis in (sdl2.SDL_CONTROLLER_AXIS_LEFTX, sdl2.SDL_CONTROLLER_AXIS_LEFTY, sdl2.SDL_CONTROLLER_AXIS_RIGHTX, sdl2.SDL_CONTROLLER_AXIS_RIGHTY):
                    if value >= 32768:
                        value = 32767
                    elif value <= -32768:
                        value = -32768
                if axis in (sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT, sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT):
                    value = int(value / 32767 * 255)

                self.set_axis(SDL_AXIS_MAP[axis], value)
