import datetime
from binascii import unhexlify
from construct import Container

import xbox.nano.packer as packer
import xbox.nano.factory as factory
import xbox.nano.packet.message as message
import xbox.nano.packet as packet
import xbox.nano.enum as enum


def test_header_tcp(packets):
    data = packets['tcp_control_handshake'][:12]

    msg = factory.header(
        payload_type=enum.RtpPayloadType.Control,
        connection_id=0, channel_id=0, timestamp=2847619159, padding=True
    )
    msg.flags(csrc_count=0, version=2, extension=False, marker=False)
    msg(sequence_num=0, csrc_list=[])
    packed = msg.build()

    assert msg.flags.version == 2
    assert msg.flags.padding is True
    assert msg.flags.extension is False
    assert msg.flags.csrc_count == 0
    assert msg.flags.marker is False
    assert msg.flags.payload_type == enum.RtpPayloadType.Control
    assert msg.sequence_num == 0
    assert msg.timestamp == 2847619159
    assert msg.ssrc.connection_id == 0
    assert msg.ssrc.channel_id == 0
    assert len(msg.csrc_list) == 0

    assert len(packed) == len(data)
    assert packed == data


def test_header_udp(packets):
    data = packets['udp_video_data'][:20]

    msg = factory.header(
        payload_type=enum.RtpPayloadType.Streamer,
        connection_id=35795, channel_id=1024, timestamp=0, padding=True,
        streamer=message.streamer(
            streamer_version=0, type=4
        ).container
    )
    msg.flags(csrc_count=0, version=2, extension=False, marker=False)
    msg(sequence_num=1, csrc_list=[])
    packed = msg.build()

    assert msg.flags.version == 2
    assert msg.flags.padding is True
    assert msg.flags.extension is False
    assert msg.flags.csrc_count == 0
    assert msg.flags.marker is False
    assert msg.flags.payload_type == enum.RtpPayloadType.Streamer
    assert msg.sequence_num == 1
    assert msg.timestamp == 0
    assert msg.ssrc.connection_id == 35795
    assert msg.ssrc.channel_id == 1024
    assert len(msg.csrc_list) == 0

    assert len(packed) == len(data)
    assert packed == data


def test_control_handshake(packets, channels):
    data = packets['tcp_control_handshake']

    msg = factory.channel.control_handshake(connection_id=40084)
    msg.header.flags(csrc_count=0, version=2, extension=False, marker=False, padding=True)
    msg.header(sequence_num=0, timestamp=2847619159, csrc_list=[])
    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.Control
    assert msg.payload.type == enum.ChannelControlPayloadType.ClientHandshake
    assert msg.payload.connection_id == 40084

    assert len(packed) == len(data)
    assert packed == data


def test_udp_handshake(packets, channels):
    data = packets['udp_handshake']

    msg = factory.udp_handshake(connection_id=35795, unknown=1)
    msg.header.flags(csrc_count=0, version=2, extension=False, marker=False, padding=True)
    msg.header(sequence_num=0, timestamp=1063270342, csrc_list=[])
    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.UDPHandshake
    assert msg.header.ssrc.connection_id == 35795

    assert msg.payload.unk == 1

    assert len(packed) == len(data)
    assert packed == data


def test_control_msg_with_header(packets, channels):
    data = packets['tcp_control_msg_with_header']

    payload = factory.control.realtime_telemetry(
        data=[
            Container(key=12, value=0),
            Container(key=7, value=0),
            Container(key=11, value=1),
            Container(key=6, value=0),
            Container(key=1, value=0),
            Container(key=5, value=52)
        ]
    )
    control_header = factory.control.control_header(
        prev_seq_dup=0, unk1=1, unk2=1406,
        opcode=enum.ControlPayloadType.RealtimeTelemetry,
        payload=payload.container
    )
    msg = factory.streamer_tcp(
        sequence_num=1, prev_sequence_num=0,
        payload_type=0, payload=control_header
    )
    msg.header.flags(csrc_count=0)
    msg.header.ssrc(channel_id=1027)

    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert msg.header.streamer.streamer_version == 3
    assert msg.header.streamer.sequence_num == 1
    assert msg.header.streamer.prev_sequence_num == 0
    assert msg.header.streamer.type == 0

    assert msg.payload.prev_seq_dup == 0
    assert msg.payload.unk1 == 1
    assert msg.payload.unk2 == 1406
    assert msg.payload.opcode == enum.ControlPayloadType.RealtimeTelemetry

    assert len(packed) == len(data)
    assert packed == data


def test_control_msg_with_header_change_video_quality(packets, channels):
    data = packets['tcp_control_msg_with_header_change_video_quality']

    payload = factory.control.change_video_quality(
        3000001, 1, 30000, 1001, 3600, 0
    )

    control_header = factory.control.control_header(
        prev_seq_dup=2,
        unk1=1,
        unk2=1406,
        opcode=enum.ControlPayloadType.ChangeVideoQuality,
        payload=payload.container
    )

    msg = factory.streamer_tcp(
        sequence_num=3, prev_sequence_num=2,
        payload_type=0, payload=control_header
    )

    msg.header.ssrc(channel_id=1027)
    msg.header(sequence_num=2, timestamp=852112921)
    packed = packer.pack_tcp([msg], channels)

    assert msg.header.streamer.streamer_version == 3
    assert msg.header.streamer.sequence_num == 3
    assert msg.header.streamer.prev_sequence_num == 2
    assert msg.header.streamer.type == 0

    assert msg.payload.prev_seq_dup == 2
    assert msg.payload.unk1 == 1
    assert msg.payload.unk2 == 1406
    assert msg.payload.opcode == enum.ControlPayloadType.ChangeVideoQuality

    assert len(packed) == len(data)
    assert packed == data


def test_channel_open_no_flags(packets, channels):
    data = packets['tcp_channel_open_no_flags']

    msg = factory.channel.open(flags=b'', channel_id=1024)
    msg.header.flags(csrc_count=0, version=2, extension=False, marker=False, padding=False)
    msg.header(sequence_num=0, timestamp=1965050624, csrc_list=[])
    msg.payload(name=None)

    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.ChannelControl

    assert msg.payload.type == enum.ChannelControlPayloadType.ChannelOpen
    assert msg.payload.flags == b''

    assert len(packed) == len(data)
    assert packed == data


def test_channel_open_with_flags(packets, channels):
    data = packets['tcp_channel_open_with_flags']

    msg = factory.channel.open(flags=b'\x01\x00\x02\x00', channel_id=1027)
    msg.header.flags(csrc_count=0, version=2, extension=False, marker=False, padding=False)
    msg.header(sequence_num=0, timestamp=0, csrc_list=[])
    msg.payload(name=None)

    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.ChannelControl

    assert msg.payload.type == enum.ChannelControlPayloadType.ChannelOpen
    assert msg.payload.flags == b'\x01\x00\x02\x00'

    assert len(packed) == len(data)
    assert packed == data


def test_channel_create(packets, channels):
    data = packets['tcp_channel_create']

    msg = factory.channel.create(
        name=enum.ChannelClass.Video,
        flags=0, channel_id=1024
    )
    msg.header.flags(
        csrc_count=0, version=2, extension=False,
        marker=False, padding=False
    )
    msg.header(sequence_num=0, timestamp=0, csrc_list=[])

    packed = packer.pack(msg, channels)
    assert msg.header.flags.payload_type == enum.RtpPayloadType.ChannelControl

    assert msg.payload.container.type == enum.ChannelControlPayloadType.ChannelCreate
    assert msg.payload.container.name == enum.ChannelClass.Video
    assert msg.payload.container.flags == 0

    assert len(packed) == len(data)
    assert packed == data


def test_channel_close(packets, channels):
    data = packets['tcp_channel_close']

    msg = factory.channel.close(flags=0, channel_id=1025)
    msg.header.flags(csrc_count=0, version=2, extension=False, marker=False, padding=False)
    msg.header(sequence_num=0, timestamp=2376737668, csrc_list=[])
    msg.payload(name=None)

    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.ChannelControl

    assert msg.payload.type == enum.ChannelControlPayloadType.ChannelClose
    assert msg.payload.flags == 0

    assert len(packed) == len(data)
    assert packed == data


def test_audio_client_handshake(packets, channels):
    data = packets['tcp_audio_client_handshake']

    requested_format = packet.audio.fmt(
        channels=2, sample_rate=48000, codec=1
    )
    payload = factory.audio.client_handshake(
        initial_frame_id=693041842,
        requested_format=requested_format.container
    )
    msg = factory.streamer_tcp(
        sequence_num=1, prev_sequence_num=0,
        payload_type=enum.AudioPayloadType.ClientHandshake,
        payload=payload
    )
    msg.header.flags(
        csrc_count=0, version=2, extension=False,
        marker=False, padding=False
    )
    msg.header.ssrc(channel_id=1025)
    msg.header(sequence_num=0, timestamp=1055413470, csrc_list=[])

    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert msg.header.streamer.streamer_version == 3
    assert msg.header.streamer.sequence_num == 1
    assert msg.header.streamer.prev_sequence_num == 0
    assert msg.header.streamer.type == enum.AudioPayloadType.ClientHandshake

    assert msg.payload.initial_frame_id == 693041842
    assert msg.payload.requested_format.channels == 2
    assert msg.payload.requested_format.sample_rate == 48000
    assert msg.payload.requested_format.codec == 1

    assert len(packed) == len(data)
    assert packed == data


def test_audio_server_handshake(packets, channels):
    data = packets['tcp_audio_server_handshake']

    format = packet.audio.fmt(channels=2, sample_rate=48000, codec=1)
    ref_ts = datetime.datetime.utcfromtimestamp(1495315092424 / 1000)

    payload = factory.audio.server_handshake(
        protocol_version=4, reference_timestamp=ref_ts,
        formats=[format.container]
    )
    msg = factory.streamer_tcp(
        sequence_num=1, prev_sequence_num=0,
        payload_type=enum.AudioPayloadType.ServerHandshake,
        payload=payload
    )
    msg.header.flags(
        csrc_count=0, version=2, extension=False,
        marker=False, padding=False
    )
    msg.header.ssrc(channel_id=1025)
    msg.header(sequence_num=0, timestamp=0, csrc_list=[])

    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert msg.header.streamer.streamer_version == 3
    assert msg.header.streamer.sequence_num == 1
    assert msg.header.streamer.prev_sequence_num == 0
    assert msg.header.streamer.type == enum.AudioPayloadType.ServerHandshake

    assert msg.payload.protocol_version == 4
    assert msg.payload.reference_timestamp == ref_ts
    assert len(msg.payload.formats) == 1
    assert msg.payload.formats[0].channels == 2
    assert msg.payload.formats[0].sample_rate == 48000
    assert msg.payload.formats[0].codec == 1

    assert len(packed) == len(data)
    assert packed == data


def test_audio_control(packets, channels):
    data = packets['tcp_audio_control']

    payload = factory.audio.control(
        reinitialize=False, start_stream=True, stop_stream=False
    )
    msg = factory.streamer_tcp(
        sequence_num=2, prev_sequence_num=1,
        payload_type=enum.AudioPayloadType.Control,
        payload=payload.container
    )
    msg.header.flags(
        csrc_count=0, version=2, extension=False,
        marker=False, padding=False
    )
    msg.header(sequence_num=1, timestamp=3916375209, csrc_list=[])
    msg.header.ssrc(channel_id=1025)

    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert msg.header.streamer.streamer_version == 3
    assert msg.header.streamer.sequence_num == 2
    assert msg.header.streamer.prev_sequence_num == 1
    assert msg.header.streamer.type == enum.AudioPayloadType.Control

    assert msg.payload.flags.reinitialize is False
    assert msg.payload.flags.start_stream is True
    assert msg.payload.flags.stop_stream is False

    assert len(packed) == len(data)
    assert packed == data


def test_audio_data(packets, channels):
    data = packets['udp_audio_data']

    audio_data = unhexlify(
        b'211acffffffffffe95b5d320d4382b0d440136952aad9a464d0b8a97dd894d6eb5dd0669f1390b'
        b'2bb3855d2f1d77f105ae59071876e3a73c724f16706dd590c7f3ffbafb9b1f3bca6b38679d57b7'
        b'1559da5b5fe7b64ccadca94bace6aa5030559487cc9152df49c8da66326aa4d05920f758e309cc'
        b'd7475153653a7df16d5ad716a882b904d52db22fb535a8767e2afa37aa683284ea7996e8b44cc1'
        b'b9c88688493a2f3ccc5a247268abbd6b11b0b28930cd7a55228c0155201bf53fb66257a3a028ec'
        b'0dd476963376d18877f4eb36152d54c5374f599d388b167412a10bae75a3f2a7218dbaf0a30ea9'
        b'89224494307cd02025a72629332aa70235e4922a53f2a91752cca7e7145ef4e4926a02c928e18a'
        b'1a210dcc3342a31db0d1251649a2e8f3b5cf4885b4600daee6e664e2950d12f4c3baff32157ced'
        b'710b75545fc7db05b512267f22f853b5708dd876eeed9b18c63373f0bc019efed6739004b2103e'
        b'800f5bed48f8'
    )

    payload = factory.audio.data(
        flags=4, frame_id=0, timestamp=3365588462, data=audio_data
    )
    msg = factory.streamer_udp(
        payload_type=enum.AudioPayloadType.Data, payload=payload.container
    )
    msg.header.flags(
        csrc_count=0, version=2, extension=False,
        marker=False, padding=True
    )
    msg.header(sequence_num=1, timestamp=118137370, csrc_list=[])
    msg.header.ssrc(channel_id=1025, connection_id=35795)

    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert msg.header.streamer.streamer_version == 0
    assert msg.header.streamer.type == enum.AudioPayloadType.Data

    assert msg.payload.flags == 4
    assert msg.payload.frame_id == 0
    assert msg.payload.timestamp == 3365588462
    assert len(msg.payload.data) == 357

    assert len(packed) == len(data)
    assert packed == data


def test_video_client_handshake(packets, channels):
    data = packets['tcp_video_client_handshake']

    requested_format = packet.video.fmt(
        fps=30, width=1280, height=720, codec=0
    )
    payload = factory.video.client_handshake(
        initial_frame_id=3715731054,
        requested_format=requested_format.container
    )
    msg = factory.streamer_tcp(
        sequence_num=1, prev_sequence_num=0,
        payload_type=enum.VideoPayloadType.ClientHandshake,
        payload=payload
    )
    msg.header.flags(
        csrc_count=0, version=2, extension=False,
        marker=False, padding=False
    )
    msg.header.ssrc(channel_id=1024)
    msg.header(sequence_num=0, timestamp=1055413470, csrc_list=[])

    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert msg.header.streamer.streamer_version == 3
    assert msg.header.streamer.sequence_num == 1
    assert msg.header.streamer.prev_sequence_num == 0
    assert msg.header.streamer.type == enum.VideoPayloadType.ClientHandshake

    assert msg.payload.initial_frame_id == 3715731054
    assert msg.payload.requested_format.fps == 30
    assert msg.payload.requested_format.width == 1280
    assert msg.payload.requested_format.height == 720
    assert msg.payload.requested_format.codec == 0

    assert len(packed) == len(data)
    assert packed == data


def test_video_server_handshake(packets, channels):
    data = packets['tcp_video_server_handshake']

    ref_ts = datetime.datetime.utcfromtimestamp(1495315092425 / 1000)

    formats = [
        packet.video.fmt(fps=30, width=1280, height=720, codec=0).container,
        packet.video.fmt(fps=30, width=960, height=540, codec=0).container,
        packet.video.fmt(fps=30, width=640, height=360, codec=0).container,
        packet.video.fmt(fps=30, width=320, height=180, codec=0).container
    ]

    payload = factory.video.server_handshake(
        protocol_version=5, width=1280, height=720, fps=30,
        reference_timestamp=ref_ts, formats=formats)
    msg = factory.streamer_tcp(
        sequence_num=1, prev_sequence_num=0,
        payload_type=enum.VideoPayloadType.ServerHandshake,
        payload=payload.container
    )
    msg.header.flags(
        csrc_count=0, version=2, extension=False,
        marker=False, padding=False
    )
    msg.header.ssrc(channel_id=1024)
    msg.header(sequence_num=0, timestamp=0, csrc_list=[])

    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert msg.header.streamer.streamer_version == 3
    assert msg.header.streamer.sequence_num == 1
    assert msg.header.streamer.prev_sequence_num == 0
    assert msg.header.streamer.type == enum.VideoPayloadType.ServerHandshake

    assert msg.payload.protocol_version == 5
    assert msg.payload.width == 1280
    assert msg.payload.height == 720
    assert msg.payload.fps == 30
    assert msg.payload.reference_timestamp == ref_ts
    assert len(msg.payload.formats) == 4

    assert msg.payload.formats[0].fps == 30
    assert msg.payload.formats[0].width == 1280
    assert msg.payload.formats[0].height == 720
    assert msg.payload.formats[0].codec == 0
    assert msg.payload.formats[1].fps == 30
    assert msg.payload.formats[1].width == 960
    assert msg.payload.formats[1].height == 540
    assert msg.payload.formats[1].codec == 0
    assert msg.payload.formats[2].fps == 30
    assert msg.payload.formats[2].width == 640
    assert msg.payload.formats[2].height == 360
    assert msg.payload.formats[2].codec == 0
    assert msg.payload.formats[3].fps == 30
    assert msg.payload.formats[3].width == 320
    assert msg.payload.formats[3].height == 180
    assert msg.payload.formats[3].codec == 0

    assert len(packed) == len(data)
    assert packed == data


def test_video_control(packets, channels):
    data = packets['tcp_video_control']

    payload = factory.video.control(
        request_keyframe=True, start_stream=True
    )
    msg = factory.streamer_tcp(
        sequence_num=2, prev_sequence_num=1,
        payload_type=enum.VideoPayloadType.Control,
        payload=payload.container
    )
    msg.header.flags(
        csrc_count=0, version=2, extension=False,
        marker=False, padding=False
    )
    msg.header(sequence_num=1, timestamp=188277389, csrc_list=[])
    msg.header.ssrc(channel_id=1024)

    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert msg.header.streamer.streamer_version == 3
    assert msg.header.streamer.sequence_num == 2
    assert msg.header.streamer.prev_sequence_num == 1
    assert msg.header.streamer.type == enum.VideoPayloadType.Control

    assert msg.payload.flags.request_keyframe is True
    assert msg.payload.flags.start_stream is True
    assert msg.payload.flags.stop_stream is False
    assert msg.payload.flags.queue_depth is False
    assert msg.payload.flags.lost_frames is False
    assert msg.payload.flags.last_displayed_frame is False

    assert len(packed) == len(data)
    assert packed == data


def test_video_data(packets, channels):
    data = packets['udp_video_data']

    video_data = unhexlify(
        b'00000001419aaec42f7fc4a01aedf7b54a29887e0a42aa07a6bc7c52e93dc52a2b6c0bbc51499f'
        b'ff4b0d94eb5cc6fb60753ece94b6dda09d0f87f870c7f443e4c44cd1c8e0a0f199930cfb092483'
        b'8143c782bfc85a429009aca280b0918df400898005ea2e87474461632cb9c40ec68e91f08aa643'
        b'2d6801f51539bd85fa2b58cef47237c90a6ab1a594481a036ba7e4823c59d244d47387033e97f6'
        b'8c0cd6d92d7053bc24b23aa6c8e681828332fe14f33630135b7084cd0c66761969686ae68c3267'
        b'b2cc0a04648e250d57bc72f4eed83754a66746d63fe5039c0dbcf6d91e9c2e9c06b12b347d8ef2'
        b'b548a3a71894ccbce971ffb97fd603295afb77619a2edf0c8dbca6bf34d0ba576260965a6b1c71'
        b'c2e78b9ffffbfe2a3e4f074bd7dee2673239ae4f2dda79a8b0fbf50155826a53eada60d22b45af'
        b'a5309acd3fcc2e0c9da11a0c22784cb7eaeff9305b953e66e3dd1ba6353d27457971bad05caa2d'
        b'eaa9b7ade9af8a1447edd78929c298978a884053c049d1889938250a2a1971cb5983fcce03c2ec'
        b'f5771d467d5ce17008138d3098724c91642bfb0c5c1dfc2e6ec0f7e4e4a82683997b8b7ef9ce7c'
        b'612af61368b1378a0eadf9427cea0c508d1c59290827051f7101900fc58d3d5e1c77092186e709'
        b'e4725ff6568127f4ba79d819d8887d7cebe23902db27db505212d2e1cd36234132aa3a761355d8'
        b'64345eba9bba6c50481f52e26f035e4561e7222cb7088ed7b443d9b6086ca5cabe17d49d03d3ef'
        b'2aac9111af79d31ba9fae05fa95edf4290824eee803c5e8d40a7e7ce4fa21d0388705fc7cc1c5a'
        b'42c827f8775fef6d7b50a6fe72e04d51f0d52bbc838a1ac4bedd2eaeef994dbc06f39db5f7644b'
        b'f6e69a75fd25be1bf696f9d34b5b107fad2dffed8b71f3aa4560959c1de9e0bb235b58f51dafe8'
        b'ff922b8cd35d763c338f40f88ad10cec7305b107ba19404f9cba053efa2cef72cb91e44e845b3c'
        b'ffdf13e4102e4a2900bba4ca367f0ac08de2aa2232ee5f59e3bbde466d434d6e12e9069667f829'
        b'0a5ac2f042614db651ecca2f4ed1e73deeccc8e83e8c9cda998b3da6175a81cf7c4229c75686a8'
        b'fcc185d591af5e61259771fd7d9c7664ce9bdfd864dc1502501ff011decbdfec0eccf03f388966'
        b'49597c070a923aeaece7a1e17ec659cc0390f96b59cd5373ae655c30897c9ddbab43485a26dcf6'
        b'ec0d07439da73ce26d9cf89b40f5b7ca221407037f995c43eab38565cc9037643ad1ccd6dc4f6e'
        b'5fb47caa2fc378ff43fc0f668527e2316f6419fde0f7e3320a6afcf7946e14c43695b28f6dc26d'
        b'34b268d13c58d6a9d52f9b6e08551b194b0f76e823fa1d7ce8af88146901646db6c7731ed43edd'
        b'771c077360f5f6114ca12216c2b498c6b71c277b64f27a703f2d51c1401ea5a8deefef1d00f169'
        b'c7b42e93fdf0c430f87b9115ff7e2f0fd3c9aeb62095a0a6d4e37c1eae886432a94a8bab2015f6'
        b'f72a902f392a365108d0d1351eec0e659fe78336b689456f65e53dab09ba8a32a2649b36066331'
        b'8d1b90253cefcda67669806f286ea2c9a9468791e1a39c8547ca98'
    )

    payload = factory.video.data(
        flags=4, frame_id=3715731054, timestamp=3365613642,
        total_size=5594, packet_count=5, offset=0, data=video_data
    )
    msg = factory.streamer_udp(
        payload_type=enum.VideoPayloadType.Data, payload=payload.container
    )
    msg.header.flags(
        csrc_count=0, version=2, extension=False,
        marker=False, padding=True
    )
    msg.header(sequence_num=1, timestamp=0, csrc_list=[])
    msg.header.ssrc(channel_id=1024, connection_id=35795)

    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert msg.header.streamer.streamer_version == 0
    assert msg.header.streamer.type == enum.VideoPayloadType.Data

    assert msg.payload.flags == 4
    assert msg.payload.frame_id == 3715731054
    assert msg.payload.timestamp == 3365613642
    assert msg.payload.total_size == 5594
    assert msg.payload.packet_count == 5
    assert msg.payload.offset == 0
    assert len(msg.payload.data) == 1119

    assert len(packed) == len(data)
    assert packed == data


def test_input_client_handshake(packets, channels):
    data = packets['tcp_input_client_handshake']

    ref_ts = datetime.datetime.utcfromtimestamp(1498690645999 / 1000)

    payload = factory.input.client_handshake(
        max_touches=10, reference_timestamp=ref_ts
    )
    msg = factory.streamer_tcp(
        sequence_num=1, prev_sequence_num=0,
        payload_type=enum.InputPayloadType.ClientHandshake,
        payload=payload
    )
    msg.header.flags(
        csrc_count=0, version=2, extension=False,
        marker=False, padding=False
    )
    msg.header.ssrc(channel_id=1028)
    msg.header(sequence_num=0, timestamp=2376737668, csrc_list=[])

    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert msg.header.streamer.streamer_version == 3
    assert msg.header.streamer.sequence_num == 1
    assert msg.header.streamer.prev_sequence_num == 0
    assert msg.header.streamer.type == enum.InputPayloadType.ClientHandshake

    assert msg.payload.max_touches == 10
    assert msg.payload.reference_timestamp == ref_ts

    assert len(packed) == len(data)
    assert packed == data


def test_input_server_handshake(packets, channels):
    data = packets['tcp_input_server_handshake']

    payload = factory.input.server_handshake(
        protocol_version=3,
        desktop_width=1280,
        desktop_height=720,
        max_touches=0,
        initial_frame_id=672208545
    )
    msg = factory.streamer_tcp(
        sequence_num=1, prev_sequence_num=0,
        payload_type=enum.InputPayloadType.ServerHandshake,
        payload=payload.container
    )
    msg.header.flags(
        csrc_count=0, version=2, extension=False,
        marker=False, padding=False
    )
    msg.header.ssrc(channel_id=1028)
    msg.header(sequence_num=0, timestamp=360018603, csrc_list=[])

    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert msg.header.streamer.streamer_version == 3
    assert msg.header.streamer.sequence_num == 1
    assert msg.header.streamer.prev_sequence_num == 0
    assert msg.header.streamer.type == enum.InputPayloadType.ServerHandshake

    assert msg.payload.protocol_version == 3
    assert msg.payload.desktop_width == 1280
    assert msg.payload.desktop_height == 720
    assert msg.payload.max_touches == 0
    assert msg.payload.initial_frame_id == 672208545

    assert len(packed) == len(data)
    assert packed == data


def test_input_frame_ack(packets, channels):
    data = packets['udp_input_frame_ack']

    payload = factory.input.frame_ack(acked_frame=672208545)
    msg = factory.streamer_udp(
        payload_type=enum.InputPayloadType.FrameAck,
        payload=payload.container
    )
    msg.header.flags(
        csrc_count=0, version=2, extension=False,
        marker=False, padding=False
    )
    msg.header(sequence_num=1, timestamp=360018616, csrc_list=[])
    msg.header.ssrc(channel_id=1028, connection_id=56147)

    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert msg.header.streamer.streamer_version == 0
    assert msg.header.streamer.type == enum.InputPayloadType.FrameAck

    assert msg.payload.acked_frame == 672208545

    assert len(packed) == len(data)
    assert packed == data


def test_input_frame(packets, channels):
    data = packets['udp_input_frame']

    buttons = packet.input.input_frame_buttons(
        dpad_up=0,
        dpad_down=0,
        dpad_left=0,
        dpad_right=1,
        start=0,
        back=0,
        left_thumbstick=0,
        right_thumbstick=0,
        left_shoulder=0,
        right_shoulder=0,
        guide=0,
        unknown=0,
        a=0,
        b=0,
        x=0,
        y=0
    )
    analog = packet.input.input_frame_analog(
        left_trigger=0,
        right_trigger=0,
        left_thumb_x=1752,
        left_thumb_y=684,
        right_thumb_x=1080,
        right_thumb_y=242,
        rumble_trigger_l=0,
        rumble_trigger_r=0,
        rumble_handle_l=0,
        rumble_handle_r=0
    )
    extension = packet.input.input_frame_extension(
        byte_6=1,
        byte_7=0,
        rumble_trigger_l2=0,
        rumble_trigger_r2=0,
        rumble_handle_l2=0,
        rumble_handle_r2=0,
        byte_12=0,
        byte_13=0,
        byte_14=0
    )
    payload = packet.input.frame(
        frame_id=672208564, timestamp=583706515, created_ts=583706495,
        buttons=buttons.container, analog=analog.container,
        extension=extension.container
    )
    msg = factory.streamer_udp(
        payload_type=enum.InputPayloadType.Frame,
        payload=payload.container
    )
    msg.header.flags(
        csrc_count=0, version=2, extension=False,
        marker=False, padding=True
    )
    msg.header(sequence_num=2, timestamp=2376737668, csrc_list=[])
    msg.header.ssrc(channel_id=1028, connection_id=56147)

    packed = packer.pack(msg, channels)

    assert msg.header.flags.payload_type == enum.RtpPayloadType.Streamer

    assert msg.header.streamer.streamer_version == 0
    assert msg.header.streamer.type == enum.InputPayloadType.Frame

    assert msg.payload.frame_id == 672208564
    assert msg.payload.timestamp == 583706515
    assert msg.payload.created_ts == 583706495
    assert msg.payload.buttons.dpad_up == 0
    assert msg.payload.buttons.dpad_down == 0
    assert msg.payload.buttons.dpad_left == 0
    assert msg.payload.buttons.dpad_right == 1
    assert msg.payload.buttons.start == 0
    assert msg.payload.buttons.back == 0
    assert msg.payload.buttons.left_thumbstick == 0
    assert msg.payload.buttons.right_thumbstick == 0
    assert msg.payload.buttons.left_shoulder == 0
    assert msg.payload.buttons.right_shoulder == 0
    assert msg.payload.buttons.guide == 0
    assert msg.payload.buttons.unknown == 0
    assert msg.payload.buttons.a == 0
    assert msg.payload.buttons.b == 0
    assert msg.payload.buttons.x == 0
    assert msg.payload.buttons.y == 0
    assert msg.payload.analog.left_trigger == 0
    assert msg.payload.analog.right_trigger == 0
    assert msg.payload.analog.left_thumb_x == 1752
    assert msg.payload.analog.left_thumb_y == 684
    assert msg.payload.analog.right_thumb_x == 1080
    assert msg.payload.analog.right_thumb_y == 242
    assert msg.payload.analog.rumble_trigger_l == 0
    assert msg.payload.analog.rumble_trigger_r == 0
    assert msg.payload.analog.rumble_handle_l == 0
    assert msg.payload.analog.rumble_handle_r == 0
    assert msg.payload.extension.byte_6 == 1
    assert msg.payload.extension.byte_7 == 0
    assert msg.payload.extension.rumble_trigger_l2 == 0
    assert msg.payload.extension.rumble_trigger_r2 == 0
    assert msg.payload.extension.rumble_handle_l2 == 0
    assert msg.payload.extension.rumble_handle_r2 == 0
    assert msg.payload.extension.byte_12 == 0
    assert msg.payload.extension.byte_13 == 0
    assert msg.payload.extension.byte_14 == 0

    assert len(packed) == len(data)
    assert packed == data
