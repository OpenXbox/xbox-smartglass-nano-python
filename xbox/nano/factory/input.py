import construct
from xbox.nano.packet import input


def server_handshake(protocol_version, desktop_width, desktop_height,
                     max_touches, initial_frame_id):
    return input.server_handshake(
        protocol_version=protocol_version,
        desktop_width=desktop_width,
        desktop_height=desktop_height,
        max_touches=max_touches,
        initial_frame_id=initial_frame_id
    )


def client_handshake(max_touches, reference_timestamp):
    return input.client_handshake(
        max_touches=max_touches,
        reference_timestamp=reference_timestamp
    )


def frame_ack(acked_frame):
    return input.frame_ack(acked_frame=acked_frame)
