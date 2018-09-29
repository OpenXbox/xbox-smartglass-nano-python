# flake8: noqa
from construct import *
from xbox.nano.enum import RtpPayloadType, ChannelControlPayloadType, ChannelClass
from xbox.sg.utils.struct import XStruct
from xbox.sg.utils.adapters import XSwitch, XEnum, XInject, PrefixedBytes


channel_control_handshake = XStruct(
    'type' / XEnum(Int8ul, ChannelControlPayloadType),
    'connection_id' / Int16ul
)


channel_control = XStruct(
    'type' / XEnum(Int32ul, ChannelControlPayloadType),
    'name' / If(
        this.type == ChannelControlPayloadType.ChannelCreate,
        XEnum(PascalString(Int16ul, 'utf8'), ChannelClass)
    ),
    'flags' / XSwitch(
        this.type, {
            # Flags: For control channel, second Int16ul is protocol version. First doesnt seem to do anything
            ChannelControlPayloadType.ChannelCreate: Int32ul,
            ChannelControlPayloadType.ChannelOpen: PrefixedBytes(Int32ul),
            # Might be reason?
            ChannelControlPayloadType.ChannelClose: Int32ul
        }
    )
)


udp_handshake = XStruct(
    'unk' / Byte
)


streamer = XStruct(
    'streamer_version' / Int32ul,  # Probably
    'sequence_num' / If(this.streamer_version & 1, Int32ul),
    'prev_sequence_num' / If(this.streamer_version & 1, Int32ul),
    'type' / XEnum(Int32ul)
)


# Based on RTP header
header = XStruct(
    XInject('from xbox.nano.enum import RtpPayloadType'),
    'flags' / BitStruct(
        'version' / Default(BitsInteger(2), 2),
        'padding' / Default(Flag, False),
        'extension' / Default(Flag, False),
        'csrc_count' / Default(BitsInteger(4), 0),
        'marker' / Default(Flag, False),
        'payload_type' / XEnum(BitsInteger(7), RtpPayloadType)
    ),
    'sequence_num' / Default(Int16ub, 0),
    'timestamp' / Default(Int32ub, 0),
    'ssrc' / Struct(
        'connection_id' / Int16ub,
        'channel_id' / Int16ub
    ),
    'csrc_list' / Default(Array(this.flags.csrc_count, Int32ub), []),
    'streamer' / If(
        this.flags.payload_type == RtpPayloadType.Streamer,
        streamer
    )
)


struct = XStruct(
    'header' / header,
    'payload' / XSwitch(this.header.flags.payload_type, {
        RtpPayloadType.Control: channel_control_handshake,
        RtpPayloadType.ChannelControl: channel_control,
        RtpPayloadType.UDPHandshake: udp_handshake,
        RtpPayloadType.Streamer: IfThenElse(
            this.header.ssrc.connection_id == 0 and this.header.streamer.type == 0,
            # ControlStreamer (type: 0) -> No payload length prefixed
            GreedyBytes,
            PrefixedBytes(Int32ul)
        )
    })
)


# # StreamerMessage Body - W/o Header
# session_init = Struct(
#     'streamer_version' / Int16ub,
#     'control_channel_protocol_version' / Int16ub
# )


# session_create = Struct(
#     'guid' / UUIDAdapter(),
#     'uint1' / Int32ub,
#     'rest' / GreedyBytes # TODO
# )


# session_create_response = Struct(
#     'guid' / UUIDAdapter()
# )


# session_destroy = Struct(
#     'uint1' / Int32ub,
#     'uint2' / Int32ub,
#     'rest' / GreedyBytes # TODO
# )

# initiate_network_test = Struct(
#     'guid' / UUIDAdapter()
# )


# network_information = Struct(
#     'guid' / UUIDAdapter(),
#     'ull' / Int64ub,
#     'bool' / Byte,
#     'uint' / Int32ub
# )


# network_test_response = Struct(
#     'guid' / UUIDAdapter(),
#     'uint1' / Int32ub,
#     'float1' / Float32b,
#     'uint2' / Int32ub,
#     'uint3' / Int32ub,
#     'float2' / Float32b,
#     'ull1' / Int64ub,
#     'ull2' / Int64ub,
#     'uint4' / Int32ub
# )


# video_statistics = Struct(
#     'ssrc' / Int32ub,
#     'lost_packets' / Int32ub,
#     'highest_seq_received' / Int32ub,
#     'interarrival_jitter' / Int32ub,
#     'last_sr' / Int32ub,
#     'delay_since_last_sr' / Int32ub,
# )
