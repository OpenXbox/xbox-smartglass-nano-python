from construct import Container
from xbox.nano.packet import message
from xbox.nano.enum import RtpPayloadType

STREAMER_VERSION = 3


def header(payload_type, connection_id=0, channel_id=0, timestamp=0,
           streamer=None, padding=False, sequence_num=0, **kwargs):
    """
    Helper method for creating a RTP header.
    """
    return message.header(
        flags=Container(
            padding=padding,
            payload_type=payload_type
        ),
        sequence_num=sequence_num,
        timestamp=timestamp,
        ssrc=Container(
            connection_id=connection_id,
            channel_id=channel_id
        ),
        streamer=streamer,
        **kwargs
    )


def streamer_tcp(sequence_num, prev_sequence_num,
                 payload_type, payload, **kwargs):
    return message.struct(
        header=header(
            payload_type=RtpPayloadType.Streamer,
            streamer=message.streamer(
                streamer_version=STREAMER_VERSION,
                sequence_num=sequence_num,
                prev_sequence_num=prev_sequence_num,
                type=payload_type
            ), **kwargs
        ),
        payload=payload
    )


def streamer_udp(payload_type, payload, **kwargs):
    return message.struct(
        header=header(
            payload_type=RtpPayloadType.Streamer,
            streamer=message.streamer(
                streamer_version=0,
                type=payload_type
            ), **kwargs
        ),
        payload=payload
    )


def udp_handshake(connection_id, unknown=1, **kwargs):
    return message.struct(
        header=header(
            payload_type=RtpPayloadType.UDPHandshake,
            connection_id=connection_id, **kwargs
        ),
        payload=message.udp_handshake(
            unk=unknown
        )
    )
