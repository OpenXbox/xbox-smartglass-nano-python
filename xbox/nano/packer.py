from construct import Int32ul
from xbox.sg.utils.struct import flatten, XStructObj
from xbox.sg.crypto import ANSIX923Padding
from xbox.nano.packet import message, video, audio, input, control
from xbox.nano.enum import RtpPayloadType, ChannelClass, VideoPayloadType, \
    AudioPayloadType, InputPayloadType


STREAMER_TYPE_MAP = {
    ChannelClass.Video: VideoPayloadType,
    ChannelClass.Audio: AudioPayloadType,
    ChannelClass.ChatAudio: AudioPayloadType,
    ChannelClass.Input: InputPayloadType,
    ChannelClass.InputFeedback: InputPayloadType,
    ChannelClass.Control: lambda _: 0
}


PAYLOAD_TYPE_MAP = {
    ChannelClass.Video: {
        VideoPayloadType.ServerHandshake: video.server_handshake,
        VideoPayloadType.ClientHandshake: video.client_handshake,
        VideoPayloadType.Control: video.control,
        VideoPayloadType.Data: video.data
    },
    ChannelClass.Audio: {
        AudioPayloadType.ServerHandshake: audio.server_handshake,
        AudioPayloadType.ClientHandshake: audio.client_handshake,
        AudioPayloadType.Control: audio.control,
        AudioPayloadType.Data: audio.data
    },
    ChannelClass.ChatAudio: {
        AudioPayloadType.ServerHandshake: audio.server_handshake,
        AudioPayloadType.ClientHandshake: audio.client_handshake,
        AudioPayloadType.Control: audio.control,
        AudioPayloadType.Data: audio.data
    },
    ChannelClass.Input: {
        InputPayloadType.ServerHandshake: input.server_handshake,
        InputPayloadType.ClientHandshake: input.client_handshake,
        InputPayloadType.FrameAck: input.frame_ack,
        InputPayloadType.Frame: input.frame
    },
    ChannelClass.InputFeedback: {
        InputPayloadType.ServerHandshake: input.server_handshake,
        InputPayloadType.ClientHandshake: input.client_handshake,
        InputPayloadType.FrameAck: input.frame_ack,
        InputPayloadType.Frame: input.frame
    },
    ChannelClass.Control: {
        0: control.control_packet
    }
}


def unpack_tcp(buf, channels=None):
    while len(buf):
        size = Int32ul.parse(buf)
        msg, buf = buf[4:size + 4], buf[size + 4:]
        yield unpack(msg, channels)


def pack_tcp(msgs, channels=None):
    buf = b''

    for msg in msgs:
        msg = pack(msg, channels)
        buf += Int32ul.build(len(msg)) + msg

    return buf


def unpack(buf, channels=None):
    # Padding is ignored
    msg = message.struct.parse(buf)

    if msg.header.flags.payload_type == RtpPayloadType.Streamer:
        payload_struct = _find_channel_payload(msg, channels)
        payload = payload_struct.parse(msg.payload)

        return msg(payload=payload)
    return msg


def pack(msg, channels=None):
    container = flatten(msg.container)

    # streamer = b''
    payload = b''
    if msg.header.flags.payload_type == RtpPayloadType.Streamer:
        # streamer = msg.subcon.streamer.build(container.streamer, **container)

        if isinstance(msg.payload, XStructObj):
            payload = msg.payload.build(**container)
        else:
            payload_struct = _find_channel_payload(msg, channels)
            payload = payload_struct.build(container.payload, **container)
        container.payload = payload

    payload = msg.subcon.payload.build(container.payload, **container)
    if ANSIX923Padding.size(len(payload), 4) > 0:
        msg.container.header.flags.padding = True
        payload = ANSIX923Padding.pad(payload, 4)

    buf = msg.subcon.header.build(container.header, **container.header)
    # buf += streamer
    buf += payload

    return buf


def _find_channel_payload(msg, channels):
    if not channels:
        raise ValueError('No channels passed')

    channel_id = msg.header.ssrc.channel_id
    if channel_id not in channels:
        raise ValueError('Unknown channel ID %d' % channel_id)

    channel = channels[channel_id]

    if channel.name not in PAYLOAD_TYPE_MAP:
        raise ValueError('Unknown channel class %s' % channel.name)

    streamer_type = msg.header.streamer.type
    if isinstance(streamer_type, int):
        streamer_type = msg.header.streamer.type = STREAMER_TYPE_MAP[channel.name](streamer_type)

    if streamer_type not in PAYLOAD_TYPE_MAP[channel.name]:
        raise ValueError('Unknown streamer type %r' % streamer_type)

    return PAYLOAD_TYPE_MAP[channel.name][streamer_type]
