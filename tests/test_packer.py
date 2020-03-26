import datetime
from binascii import hexlify

from xbox.nano import packer, enum
from xbox.nano.packet import message



def test_rtpheader_tcp(packets, channels):
    unpacked = packer.unpack(packets['tcp_control_handshake'], channels)

    assert unpacked.header.flags.version, 2
    assert unpacked.header.flags.padding is True
    assert unpacked.header.flags.extension is False
    assert unpacked.header.flags.csrc_count == 0
    assert unpacked.header.flags.marker is False
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.Control
    assert unpacked.header.sequence_num == 0
    assert unpacked.header.timestamp == 2847619159
    assert unpacked.header.ssrc.connection_id == 0
    assert unpacked.header.ssrc.channel_id == 0
    assert len(unpacked.header.csrc_list) == 0


def test_rtpheader_udp(packets, channels):
    unpacked = packer.unpack(packets['udp_video_data'], channels)

    assert unpacked.header.flags.version == 2
    assert unpacked.header.flags.padding is True
    assert unpacked.header.flags.extension is False
    assert unpacked.header.flags.csrc_count == 0
    assert unpacked.header.flags.marker is False
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.Streamer
    assert unpacked.header.sequence_num == 1
    assert unpacked.header.timestamp == 0
    assert unpacked.header.ssrc.connection_id == 35795
    assert unpacked.header.ssrc.channel_id == 1024
    assert len(unpacked.header.csrc_list) == 0


def test_control_handshake(packets, channels):
    unpacked = packer.unpack(packets['tcp_control_handshake'], channels)

    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.Control
    assert unpacked.payload.type == enum.ChannelControlPayloadType.ClientHandshake
    assert unpacked.payload.connection_id == 40084


def test_udp_handshake(packets, channels):
    unpacked = packer.unpack(packets['udp_handshake'], channels)

    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.UDPHandshake
    assert unpacked.header.ssrc.connection_id == 35795

    assert unpacked.payload.unk == 1


def test_control_msg_with_header(packets, channels):
    unpacked = packer.unpack(packets['tcp_control_msg_with_header'], channels)
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert unpacked.header.streamer.streamer_version == 3
    assert unpacked.header.streamer.sequence_num == 1
    assert unpacked.header.streamer.prev_sequence_num == 0
    assert unpacked.header.streamer.type == 0

    assert unpacked.payload.prev_seq_dup == 0
    assert unpacked.payload.unk1 == 1
    assert unpacked.payload.unk2 == 1406
    assert unpacked.payload.opcode == enum.ControlPayloadType.RealtimeTelemetry


def test_channel_open_no_flags(packets, channels):
    unpacked = packer.unpack(packets['tcp_channel_open_no_flags'], channels)
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.ChannelControl

    assert unpacked.payload.type == enum.ChannelControlPayloadType.ChannelOpen
    assert unpacked.payload.flags == b''


def test_channel_open_with_flags(packets, channels):
    unpacked = packer.unpack(packets['tcp_channel_open_with_flags'], channels)
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.ChannelControl

    assert unpacked.payload.type == enum.ChannelControlPayloadType.ChannelOpen
    assert unpacked.payload.flags == b'\x01\x00\x02\x00'


def test_channel_create(packets, channels):
    unpacked = packer.unpack(packets['tcp_channel_create'], channels)
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.ChannelControl

    assert unpacked.payload.type == enum.ChannelControlPayloadType.ChannelCreate
    assert unpacked.payload.name == enum.ChannelClass.Video
    assert unpacked.payload.flags == 0


def test_channel_close(packets, channels):
    unpacked = packer.unpack(packets['tcp_channel_close'], channels)
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.ChannelControl

    assert unpacked.payload.type == enum.ChannelControlPayloadType.ChannelClose
    assert unpacked.payload.flags == 0


def test_audio_client_handshake(packets, channels):
    unpacked = packer.unpack(packets['tcp_audio_client_handshake'], channels)
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert unpacked.header.streamer.streamer_version == 3
    assert unpacked.header.streamer.sequence_num == 1
    assert unpacked.header.streamer.prev_sequence_num == 0
    assert unpacked.header.streamer.type == enum.AudioPayloadType.ClientHandshake

    assert unpacked.payload.initial_frame_id == 693041842
    assert unpacked.payload.requested_format.channels == 2
    assert unpacked.payload.requested_format.sample_rate == 48000
    assert unpacked.payload.requested_format.codec == enum.AudioCodec.AAC


def test_audio_server_handshake(packets, channels):
    unpacked = packer.unpack(packets['tcp_audio_server_handshake'], channels)
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert unpacked.header.streamer.streamer_version == 3
    assert unpacked.header.streamer.sequence_num == 1
    assert unpacked.header.streamer.prev_sequence_num == 0
    assert unpacked.header.streamer.type == enum.AudioPayloadType.ServerHandshake

    assert unpacked.payload.protocol_version == 4
    assert unpacked.payload.reference_timestamp == datetime.datetime.utcfromtimestamp(1495315092424 / 1000)
    assert len(unpacked.payload.formats) == 1
    assert unpacked.payload.formats[0].channels == 2
    assert unpacked.payload.formats[0].sample_rate == 48000
    assert unpacked.payload.formats[0].codec == enum.AudioCodec.AAC


def test_audio_control(packets, channels):
    unpacked = packer.unpack(packets['tcp_audio_control'], channels)
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert unpacked.header.streamer.streamer_version == 3
    assert unpacked.header.streamer.sequence_num == 2
    assert unpacked.header.streamer.prev_sequence_num == 1
    assert unpacked.header.streamer.type == enum.AudioPayloadType.Control

    assert unpacked.payload.flags.reinitialize is False
    assert unpacked.payload.flags.start_stream is True
    assert unpacked.payload.flags.stop_stream is False


def test_audio_data(packets, channels):
    unpacked = packer.unpack(packets['udp_audio_data'], channels)
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert unpacked.header.streamer.streamer_version == 0
    assert unpacked.header.streamer.type == enum.AudioPayloadType.Data

    assert unpacked.payload.flags == 4
    assert unpacked.payload.frame_id == 0
    assert unpacked.payload.timestamp == 3365588462
    assert len(unpacked.payload.data) == 357


def test_video_client_handshake(packets, channels):
    unpacked = packer.unpack(packets['tcp_video_client_handshake'], channels)
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert unpacked.header.streamer.streamer_version == 3
    assert unpacked.header.streamer.sequence_num == 1
    assert unpacked.header.streamer.prev_sequence_num == 0
    assert unpacked.header.streamer.type == enum.VideoPayloadType.ClientHandshake

    assert unpacked.payload.initial_frame_id == 3715731054
    assert unpacked.payload.requested_format.fps == 30
    assert unpacked.payload.requested_format.width == 1280
    assert unpacked.payload.requested_format.height == 720
    assert unpacked.payload.requested_format.codec == enum.VideoCodec.H264


def test_video_server_handshake(packets, channels):
    unpacked = packer.unpack(packets['tcp_video_server_handshake'], channels)
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert unpacked.header.streamer.streamer_version == 3
    assert unpacked.header.streamer.sequence_num == 1
    assert unpacked.header.streamer.prev_sequence_num == 0
    assert unpacked.header.streamer.type == enum.VideoPayloadType.ServerHandshake

    assert unpacked.payload.protocol_version == 5
    assert unpacked.payload.width == 1280
    assert unpacked.payload.height == 720
    assert unpacked.payload.fps == 30
    assert unpacked.payload.reference_timestamp == datetime.datetime.utcfromtimestamp(1495315092425 / 1000)
    assert len(unpacked.payload.formats) == 4

    assert unpacked.payload.formats[0].fps == 30
    assert unpacked.payload.formats[0].width == 1280
    assert unpacked.payload.formats[0].height == 720
    assert unpacked.payload.formats[0].codec == enum.VideoCodec.H264
    assert unpacked.payload.formats[1].fps == 30
    assert unpacked.payload.formats[1].width == 960
    assert unpacked.payload.formats[1].height == 540
    assert unpacked.payload.formats[1].codec == enum.VideoCodec.H264
    assert unpacked.payload.formats[2].fps == 30
    assert unpacked.payload.formats[2].width == 640
    assert unpacked.payload.formats[2].height == 360
    assert unpacked.payload.formats[2].codec == enum.VideoCodec.H264
    assert unpacked.payload.formats[3].fps == 30
    assert unpacked.payload.formats[3].width == 320
    assert unpacked.payload.formats[3].height == 180
    assert unpacked.payload.formats[3].codec == enum.VideoCodec.H264


def test_video_control(packets, channels):
    unpacked = packer.unpack(packets['tcp_video_control'], channels)
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert unpacked.header.streamer.streamer_version == 3
    assert unpacked.header.streamer.sequence_num == 2
    assert unpacked.header.streamer.prev_sequence_num == 1
    assert unpacked.header.streamer.type == enum.VideoPayloadType.Control

    assert unpacked.payload.flags.request_keyframe is True
    assert unpacked.payload.flags.start_stream is True
    assert unpacked.payload.flags.stop_stream is False
    assert unpacked.payload.flags.queue_depth is False
    assert unpacked.payload.flags.lost_frames is False
    assert unpacked.payload.flags.last_displayed_frame is False


def test_video_data(packets, channels):
    unpacked = packer.unpack(packets['udp_video_data'], channels)
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert unpacked.header.streamer.streamer_version == 0
    assert unpacked.header.streamer.type == enum.VideoPayloadType.Data

    assert unpacked.payload.flags == 4
    assert unpacked.payload.frame_id == 3715731054
    assert unpacked.payload.timestamp == 3365613642
    assert unpacked.payload.total_size == 5594
    assert unpacked.payload.packet_count == 5
    assert unpacked.payload.offset == 0
    assert len(unpacked.payload.data) == 1119


def test_input_client_handshake(packets, channels):
    unpacked = packer.unpack(packets['tcp_input_client_handshake'], channels)
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert unpacked.header.streamer.streamer_version == 3
    assert unpacked.header.streamer.sequence_num == 1
    assert unpacked.header.streamer.prev_sequence_num == 0
    assert unpacked.header.streamer.type == enum.InputPayloadType.ClientHandshake

    assert unpacked.payload.max_touches == 10
    assert unpacked.payload.reference_timestamp == datetime.datetime.utcfromtimestamp(1498690645999 / 1000)


def test_input_server_handshake(packets, channels):
    unpacked = packer.unpack(packets['tcp_input_server_handshake'], channels)
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert unpacked.header.streamer.streamer_version == 3
    assert unpacked.header.streamer.sequence_num == 1
    assert unpacked.header.streamer.prev_sequence_num == 0
    assert unpacked.header.streamer.type == enum.InputPayloadType.ServerHandshake

    assert unpacked.payload.protocol_version == 3
    assert unpacked.payload.desktop_width == 1280
    assert unpacked.payload.desktop_height == 720
    assert unpacked.payload.max_touches == 0
    assert unpacked.payload.initial_frame_id == 672208545


def test_input_frame_ack(packets, channels):
    unpacked = packer.unpack(packets['udp_input_frame_ack'], channels)
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert unpacked.header.streamer.streamer_version == 0
    assert unpacked.header.streamer.type == enum.InputPayloadType.FrameAck

    assert unpacked.payload.acked_frame == 672208545


def test_input_frame(packets, channels):
    unpacked = packer.unpack(packets['udp_input_frame'], channels)
    assert unpacked.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert unpacked.header.streamer.streamer_version == 0
    assert unpacked.header.streamer.type == enum.InputPayloadType.Frame

    assert unpacked.payload.frame_id == 672208564
    assert unpacked.payload.timestamp == 583706515
    assert unpacked.payload.created_ts == 583706495
    assert unpacked.payload.buttons.dpad_up == 0
    assert unpacked.payload.buttons.dpad_down == 0
    assert unpacked.payload.buttons.dpad_left == 0
    assert unpacked.payload.buttons.dpad_right == 1
    assert unpacked.payload.buttons.start == 0
    assert unpacked.payload.buttons.back == 0
    assert unpacked.payload.buttons.left_thumbstick == 0
    assert unpacked.payload.buttons.right_thumbstick == 0
    assert unpacked.payload.buttons.left_shoulder == 0
    assert unpacked.payload.buttons.right_shoulder == 0
    assert unpacked.payload.buttons.guide == 0
    assert unpacked.payload.buttons.unknown == 0
    assert unpacked.payload.buttons.a == 0
    assert unpacked.payload.buttons.b == 0
    assert unpacked.payload.buttons.x == 0
    assert unpacked.payload.buttons.y == 0
    assert unpacked.payload.analog.left_trigger == 0
    assert unpacked.payload.analog.right_trigger == 0
    assert unpacked.payload.analog.left_thumb_x == 1752
    assert unpacked.payload.analog.left_thumb_y == 684
    assert unpacked.payload.analog.right_thumb_x == 1080
    assert unpacked.payload.analog.right_thumb_y == 242
    assert unpacked.payload.analog.rumble_trigger_l == 0
    assert unpacked.payload.analog.rumble_trigger_r == 0
    assert unpacked.payload.analog.rumble_handle_l == 0
    assert unpacked.payload.analog.rumble_handle_r == 0
    assert unpacked.payload.extension.byte_6 == 1
    assert unpacked.payload.extension.byte_7 == 0
    assert unpacked.payload.extension.rumble_trigger_l2 == 0
    assert unpacked.payload.extension.rumble_trigger_r2 == 0
    assert unpacked.payload.extension.rumble_handle_l2 == 0
    assert unpacked.payload.extension.rumble_handle_r2 == 0
    assert unpacked.payload.extension.byte_12 == 0
    assert unpacked.payload.extension.byte_13 == 0
    assert unpacked.payload.extension.byte_14 == 0


def _test_repack_all(packets, channels):
    for f in packets:
        unpacked = packer.unpack(packets[f])
        msg = message.struct(**unpacked)
        repacked = packer.pack(msg, channels)

        assert repacked == packets[f], \
            '%s was not repacked correctly:\n(repacked)%s\n!=\n(original)%s' \
            % (f, hexlify(repacked), hexlify(packets[f]))
