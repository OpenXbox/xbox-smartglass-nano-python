from construct import Container
from xbox.nano.packet import video


def server_handshake(protocol_version, width, height, fps,
                     reference_timestamp, formats):
    return video.server_handshake(
        protocol_version=protocol_version,
        width=width, height=height, fps=fps,
        reference_timestamp=reference_timestamp,
        formats=formats
    )


def client_handshake(initial_frame_id, requested_format):
    return video.client_handshake(
        initial_frame_id=initial_frame_id,
        requested_format=requested_format
    )


# TODO: split these up in often used combinations?
# Need to figure out the different control messages used...
def control(request_keyframe=False, start_stream=False,
            stop_stream=False, queue_depth=False, lost_frames=False,
            last_displayed_frame=False, last_displayed_frame_id=0,
            timestamp=0, queue_depth_field=0, first_lost_frame=0,
            last_lost_frame=0):
    return video.control(
        flags=Container(
            request_keyframe=request_keyframe,
            start_stream=start_stream,
            stop_stream=stop_stream,
            queue_depth=queue_depth,
            lost_frames=lost_frames,
            last_displayed_frame=last_displayed_frame
        ),
        last_displayed_frame=Container(
            frame_id=last_displayed_frame_id,
            timestamp=timestamp
        ),
        queue_depth=queue_depth_field,
        lost_frames=Container(
            first=first_lost_frame,
            last=last_lost_frame
        )
    )


def data(flags, frame_id, timestamp, total_size,
         packet_count, offset, data):
    return video.data(
        flags=flags, frame_id=frame_id, timestamp=timestamp,
        total_size=total_size, packet_count=packet_count, offset=offset,
        data=data
    )
