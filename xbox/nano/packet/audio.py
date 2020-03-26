# flake8: noqa
from construct import *
from xbox.sg.utils.struct import XStruct
from xbox.sg.utils.adapters import XEnum, PrefixedBytes
from xbox.nano.enum import AudioCodec
from xbox.nano.adapters import ReferenceTimestampAdapter

fmt = XStruct(
    'channels' / Int32ul,
    'sample_rate' / Int32ul,
    'codec' / XEnum(Int32ul, AudioCodec),
    'pcm' / If(this.codec == AudioCodec.PCM, Struct(
        'bit_depth' / Int32ul,
        'type' / Int32ul  # float or integer
    ))
)


server_handshake = XStruct(
    'protocol_version' / Int32ul,
    'reference_timestamp' / ReferenceTimestampAdapter(),
    'formats' / PrefixedArray(Int32ul, fmt)
)


client_handshake = XStruct(
    'initial_frame_id' / Int32ul,
    'requested_format' / fmt
)


control = XStruct(
    'flags' / BitStruct(
        Padding(1),
        'reinitialize' / Default(Flag, False),
        Padding(1),
        'start_stream' / Default(Flag, False),
        'stop_stream' / Default(Flag, False),
        Padding(27)
    )
)


data = XStruct(
    'flags' / Int32ul,
    'frame_id' / Int32ul,
    'timestamp' / Int64ul,
    'data' / PrefixedBytes(Int32ul)
)
