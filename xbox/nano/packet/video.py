# flake8: noqa
from construct import *
from xbox.nano.enum import VideoCodec
from xbox.sg.utils.struct import XStruct
from xbox.sg.utils.adapters import XEnum, PrefixedBytes
from xbox.nano.adapters import ReferenceTimestampAdapter


fmt = XStruct(
    'fps' / Int32ul,
    'width' / Int32ul,
    'height' / Int32ul,
    'codec' / XEnum(Int32ul, VideoCodec),
    'rgb' / If(this.codec == VideoCodec.RGB, Struct(
        'bpp' / Int32ul,
        'bytes' / Int32ul,
        'red_mask' / Int64ul,
        'green_mask' / Int64ul,
        'blue_mask' / Int64ul
    ))
)


server_handshake = XStruct(
    'protocol_version' / Int32ul,
    'width' / Int32ul,
    'height' / Int32ul,
    'fps' / Int32ul,
    'reference_timestamp' / ReferenceTimestampAdapter(),
    'formats' / PrefixedArray(Int32ul, fmt)
)


client_handshake = XStruct(
    'initial_frame_id' / Int32ul,
    'requested_format' / fmt
)


control = XStruct(
    'flags' / BitStruct(
        Padding(2),
        'request_keyframe' / Default(Flag, False),
        'start_stream' / Default(Flag, False),
        'stop_stream' / Default(Flag, False),
        'queue_depth' / Default(Flag, False),
        'lost_frames' / Default(Flag, False),
        'last_displayed_frame' / Default(Flag, False),
        Padding(24),
    ),
    'last_displayed_frame' / If(this.flags.last_displayed_frame, Struct(
       'frame_id' / Int32ul,
       'timestamp' / Int64sl
    )),
    'queue_depth' / If(this.flags.queue_depth, Int32ul),
    'lost_frames' / If(this.flags.lost_frames, Struct(
       'first' / Int32ul,
       'last' / Int32ul
    ))
)


data = XStruct(
    'flags' / Int32ul,
    'frame_id' / Int32ul,
    'timestamp' / Int64ul,
    'total_size' / Int32ul,
    'packet_count' / Int32ul,
    'offset' / Int32ul,
    'data' / PrefixedBytes(Int32ul)
)
