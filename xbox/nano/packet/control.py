# flake8: noqa
from construct import *
from xbox.sg.utils.struct import XStruct
from xbox.sg.utils.adapters import XSwitch, XEnum, PrefixedBytes
from xbox.nano.enum import ControlPayloadType, ControllerEvent

"""
ControlProtocol Streamer Messages
"""


session_init = XStruct(
    'unk3' / GreedyBytes
)


session_create = XStruct(
    'guid' / Bytes(16),
    'unk3' / PrefixedBytes(Int32ul)
)


session_create_response = XStruct(
    'guid' / Bytes(16)
)


session_destroy = XStruct(
    'unk3' / Float32l,
    'unk5' / PrefixedBytes(Int32ul)
)


video_statistics = XStruct(
    'unk3' / Float32l,
    'unk4' / Float32l,
    'unk5' / Float32l,
    'unk6' / Float32l,
    'unk7' / Float32l,
    'unk8' / Float32l
)


realtime_telemetry = XStruct(
    'data' / PrefixedArray(Int16ul, Struct(
        'key' / Int16ul,
        'value' / Int64ul
    ))
)


change_video_quality = XStruct(
    'unk3' / Int32ul,
    'unk4' / Int32ul,
    'unk5' / Int32ul,
    'unk6' / Int32ul,
    'unk7' / Int32ul,
    'unk8' / Int32ul
)


initiate_network_test = XStruct(
    'guid' / Bytes(16)
)


network_information = XStruct(
    'guid' / Bytes(16),
    'unk4' / Int64ul,
    'unk5' / Int8ul,
    'unk6' / Float32l
)


network_test_response = XStruct(
    'guid' / Bytes(16),
    'unk3' / Float32l,
    'unk4' / Float32l,
    'unk5' / Float32l,
    'unk6' / Float32l,
    'unk7' / Float32l,
    'unk8' / Int64ul,
    'unk9' / Int64ul,
    'unk10' / Float32l
)


controller_event = XStruct(
    'event' / XEnum(Int8ul, ControllerEvent),
    'controller_num' / Int8ul
)


control_packet = XStruct(
    'prev_seq_dup' / Int32ul,
    'unk1' / Int16ul,
    'unk2' / Int16ul,
    'opcode' / XEnum(Int16ul, ControlPayloadType),
    'payload' / XSwitch(
        this.opcode, {
            ControlPayloadType.SessionInit: session_init,
            ControlPayloadType.SessionCreate: session_create,
            ControlPayloadType.SessionCreateResponse: session_create_response,
            ControlPayloadType.SessionDestroy: session_destroy,
            ControlPayloadType.VideoStatistics: video_statistics,
            ControlPayloadType.RealtimeTelemetry: realtime_telemetry,
            ControlPayloadType.ChangeVideoQuality: change_video_quality,
            ControlPayloadType.InitiateNetworkTest: initiate_network_test,
            ControlPayloadType.NetworkInformation: network_information,
            ControlPayloadType.NetworkTestResponse: network_test_response,
            ControlPayloadType.ControllerEvent: controller_event
        }
    )
)
