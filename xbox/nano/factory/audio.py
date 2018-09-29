from construct import Container
from xbox.nano.packet import audio


def server_handshake(protocol_version, reference_timestamp, formats):
    return audio.server_handshake(
        protocol_version=protocol_version,
        reference_timestamp=reference_timestamp,
        formats=formats
    )


def client_handshake(initial_frame_id, requested_format):
    return audio.client_handshake(
        initial_frame_id=initial_frame_id,
        requested_format=requested_format
    )


def control(reinitialize=False, start_stream=False, stop_stream=False):
    return audio.control(
        flags=Container(
            reinitialize=reinitialize,
            start_stream=start_stream,
            stop_stream=stop_stream
        )
    )


def data(flags, frame_id, timestamp, data):
    return audio.data(
        flags=flags, frame_id=frame_id, timestamp=timestamp, data=data
    )
