import time
import logging
from enum import Enum

from xbox.nano.render.sink import Sink
from xbox.nano.packet.input import frame

log = logging.getLogger(__name__)


class GamepadButtonState(Enum):
    Pressed = 1
    Released = 2


class GamepadButton(Enum):
    DPadUp = 1
    DPadDown = 2
    DPadLeft = 3
    DPadRight = 4
    Start = 5
    Back = 6
    LeftThumbstick = 7
    RightThumbstick = 8
    LeftShoulder = 9
    RightShoulder = 10
    Guide = 11
    Unknown = 12
    A = 13
    B = 14
    X = 15
    Y = 16


class GamepadAxis(Enum):
    LeftTrigger = 20
    RightTrigger = 21
    LeftThumbstick_X = 22
    LeftThumbstick_Y = 23
    RightThumbstick_X = 24
    RightThumbstick_Y = 25


class GamepadFeedback(Enum):
    LeftTriggerRumble = 30
    RightTriggerRumble = 31
    LeftHandleRumble = 32
    RightHandleRumble = 33


FRAME_MAPPING = {
    GamepadButton.DPadUp: 'dpad_up',
    GamepadButton.DPadDown: 'dpad_down',
    GamepadButton.DPadLeft: 'dpad_left',
    GamepadButton.DPadRight: 'dpad_right',
    GamepadButton.Start: 'start',
    GamepadButton.Back: 'back',
    GamepadButton.LeftThumbstick: 'left_thumbstick',
    GamepadButton.RightThumbstick: 'right_thumbstick',
    GamepadButton.LeftShoulder: 'left_shoulder',
    GamepadButton.RightShoulder: 'right_shoulder',
    GamepadButton.Guide: 'guide',
    GamepadButton.Unknown: 'unknown',
    GamepadButton.A: 'a',
    GamepadButton.B: 'b',
    GamepadButton.X: 'x',
    GamepadButton.Y: 'y',

    GamepadAxis.LeftTrigger: 'left_trigger',
    GamepadAxis.RightTrigger: 'right_trigger',
    GamepadAxis.LeftThumbstick_X: 'left_thumb_x',
    GamepadAxis.LeftThumbstick_Y: 'left_thumb_y',
    GamepadAxis.RightThumbstick_X: 'right_thumb_x',
    GamepadAxis.RightThumbstick_Y: 'right_thumb_y',

    GamepadFeedback.LeftTriggerRumble: 'rumble_trigger_l',
    GamepadFeedback.RightTriggerRumble: 'rumble_trigger_r',
    GamepadFeedback.LeftHandleRumble: 'rumble_handle_l',
    GamepadFeedback.RightHandleRumble: 'rumble_handle_r'
}


class InputError(Exception):
    pass


class InputHandler(Sink):
    def __init__(self):
        self.client = None
        self._frame = frame(byte_6=1)

        # Set all values to zero
        for field_name in FRAME_MAPPING.values():
            self._frame(**{field_name: 0})

    def open(self, client):
        self.client = client

    def send_frame(self):
        self.client.send_input(self._frame, int(time.time()))

    def controller_added(self, controller_index):
        self.client.controller_added(controller_index)

    def controller_removed(self, controller_index):
        self.client.controller_removed(controller_index)

    def set_button(self, button, state):
        field_name = FRAME_MAPPING[button]
        current_val = getattr(self._frame, field_name)

        if current_val == 0 or (current_val % 2) == 0:
            current_state = GamepadButtonState.Released
        else:
            current_state = GamepadButtonState.Pressed

        if current_state == state:
            return

        log.debug('Button: %s - %s' % (
            GamepadButton[button], GamepadButtonState[state]
        ))

        self._frame(**{field_name: current_val + 1})
        self.send_frame()

    def set_axis(self, axis, value):
        field_name = FRAME_MAPPING[axis]

        log.debug('Axis move: %s - Value: %i' % (GamepadAxis[axis], value))

        self._frame(**{field_name: value})
        self.send_frame()
