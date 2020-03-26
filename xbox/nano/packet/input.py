# flake8: noqa
from construct import *
from xbox.sg.utils.struct import XStruct
from xbox.nano.adapters import ReferenceTimestampAdapter

server_handshake = XStruct(
    'protocol_version' / Int32ul,
    'desktop_width' / Int32ul,
    'desktop_height' / Int32ul,
    'max_touches' / Int32ul,
    'initial_frame_id' / Int32ul
)


client_handshake = XStruct(
    'max_touches' / Int32ul,
    'reference_timestamp' / ReferenceTimestampAdapter()
)


frame_ack = XStruct(
    'acked_frame' / Int32ul
)


input_frame_buttons = XStruct(
    'dpad_up' / Default(Byte, 0),
    'dpad_down' / Default(Byte, 0),
    'dpad_left' / Default(Byte, 0),
    'dpad_right' / Default(Byte, 0),
    'start' / Default(Byte, 0),
    'back' / Default(Byte, 0),
    'left_thumbstick' / Default(Byte, 0),
    'right_thumbstick' / Default(Byte, 0),
    'left_shoulder' / Default(Byte, 0),
    'right_shoulder' / Default(Byte, 0),
    'guide' / Default(Byte, 0),
    'unknown' / Default(Byte, 0),
    'a' / Default(Byte, 0),
    'b' / Default(Byte, 0),
    'x' / Default(Byte, 0),
    'y' / Default(Byte, 0)
)


input_frame_analog = XStruct(
    'left_trigger' / Default(Byte, 0),
    'right_trigger' / Default(Byte, 0),
    'left_thumb_x' / Default(Int16sl, 0),
    'left_thumb_y' / Default(Int16sl, 0),
    'right_thumb_x' / Default(Int16sl, 0),
    'right_thumb_y' / Default(Int16sl, 0),
    'rumble_trigger_l' / Default(Byte, 0),
    'rumble_trigger_r' / Default(Byte, 0),
    'rumble_handle_l' / Default(Byte, 0),
    'rumble_handle_r' / Default(Byte, 0)
)


input_frame_extension = XStruct(
    'byte_6' / Default(Byte, 0),  # always 1 for gamepad stuff?
    'byte_7' / Default(Byte, 0),
    'rumble_trigger_l2' / Default(Byte, 0),
    'rumble_trigger_r2' / Default(Byte, 0),
    'rumble_handle_l2' / Default(Byte, 0),
    'rumble_handle_r2' / Default(Byte, 0),
    'byte_12' / Default(Byte, 0),
    'byte_13' / Default(Byte, 0),
    'byte_14' / Default(Byte, 0)
)


frame = XStruct(
    'frame_id' / Int32ul,
    'timestamp' / Int64ul,
    'created_ts' / Int64ul,
    'buttons' / input_frame_buttons,
    'analog' / input_frame_analog,
    # Check if remaining length is at least 9
    'extension' / input_frame_extension
)
