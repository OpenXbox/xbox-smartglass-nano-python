from xbox.nano.packet import message
from xbox.nano.factory.message import header
from xbox.nano.enum import RtpPayloadType, ChannelControlPayloadType


def control_handshake(connection_id, **kwargs):
    return message.struct(
        header=header(
            payload_type=RtpPayloadType.Control, **kwargs
        ),
        payload=message.channel_control_handshake(
            type=ChannelControlPayloadType.ClientHandshake,
            connection_id=connection_id
        )
    )


def create(name, flags, channel_id, **kwargs):
    return message.struct(
        header=header(
            payload_type=RtpPayloadType.ChannelControl,
            channel_id=channel_id, **kwargs
        ),
        payload=message.channel_control(
            type=ChannelControlPayloadType.ChannelCreate,
            name=name,
            flags=flags
        )
    )


def open(flags, channel_id, **kwargs):
    return message.struct(
        header=header(
            payload_type=RtpPayloadType.ChannelControl,
            channel_id=channel_id, **kwargs
        ),
        payload=message.channel_control(
            type=ChannelControlPayloadType.ChannelOpen,
            name=None,
            flags=flags
        )
    )


def close(flags, channel_id, **kwargs):
    return message.struct(
        header=header(
            payload_type=RtpPayloadType.ChannelControl,
            channel_id=channel_id, **kwargs
        ),
        payload=message.channel_control(
            type=ChannelControlPayloadType.ChannelClose,
            name=None,
            flags=flags
        )
    )
