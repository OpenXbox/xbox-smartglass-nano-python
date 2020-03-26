import logging
from enum import Enum
from datetime import datetime

from xbox.nano.render.sink import Sink
from xbox.nano.packet.input import frame, input_frame_buttons, input_frame_analog, input_frame_extension

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


FRAME_MAPPING_BUTTONS = {
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
}

FRAME_MAPPING_ANALOG = {
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

        # Cache for button states
        self._button_states = {k: 0 for k in FRAME_MAPPING_BUTTONS.values()}
        self._analog_states = {k: 0 for k in FRAME_MAPPING_ANALOG.values()}

    def open(self, client):
        """
        Initialize the input handler with a NanoClient instance

        Args:
            client (:class:`xbox.nano.protocol.NanoProtocol`): Instance of :class:`NanoProtocol`

        Returns:
            None
        """
        self.client = client

    def send_frame(self):
        packet = frame(
            buttons=input_frame_buttons(**self._button_states).container,
            analog=input_frame_analog(**self._analog_states).container,
            extension=input_frame_extension(**dict(byte_6=1)).container
        )
        self.client.send_input(packet, datetime.utcnow())

    def controller_added(self, controller_index):
        self.client.controller_added(controller_index)

    def controller_removed(self, controller_index):
        self.client.controller_removed(controller_index)

    def set_button(self, button, state):
        """
        Set controller button state

        Args:
            button (:class:`GamepadButton`): Member of :class:`GamepadButton`
            state (:class:`GamepadButtonState`): Member of :class:`GamepadButtonState`

        Returns:
            None
        """
        field_name = FRAME_MAPPING_BUTTONS[button]
        current_val = self._button_states[field_name]

        if current_val == 0 or (current_val % 2) == 0:
            current_state = GamepadButtonState.Released
        else:
            current_state = GamepadButtonState.Pressed

        if current_state == state:
            return

        log.debug('Button: %s - %s' % (
            GamepadButton(button), GamepadButtonState(state)
        ))

        # Cache button state
        self._button_states[field_name] = current_val + 1
        self.send_frame()

    def set_axis(self, axis, value):
        """
        Set controller analog axis value

        Args:
            axis (:class:`GamepadAxis`): Member of :class:`GamepadAxis`
            value (int): Axis position

        Returns:
            None
        """
        field_name = FRAME_MAPPING_ANALOG[axis]

        log.debug('Axis move: %s - Value: %i' % (GamepadAxis(axis), value))

        self._analog_states[field_name] = value
        self.send_frame()
