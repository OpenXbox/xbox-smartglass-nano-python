import struct
import bitstruct
from io import BytesIO
from construct import Container

from xbox.nano import enum, packer
from xbox.nano.enum import (
    RtpPayloadType, ChannelControlPayloadType, ChannelClass,
    VideoPayloadType, AudioPayloadType, InputPayloadType, ControlPayloadType,
    ControllerEvent
)

pack = packer.pack

RTP_FLAGS = bitstruct.compile('u2b1b1u4b1u7')
VIDEO_CONTROL_FLAGS = bitstruct.compile('p2b1b1b1b1b1b1p24')
AUDIO_CONTROL_FLAGS = bitstruct.compile('p1b1p1b1b1p27')

STREAMER_TYPE_MAP = {
    ChannelClass.Video: VideoPayloadType,
    ChannelClass.Audio: AudioPayloadType,
    ChannelClass.ChatAudio: AudioPayloadType,
    ChannelClass.Input: InputPayloadType,
    ChannelClass.InputFeedback: InputPayloadType,
    ChannelClass.Control: lambda _: 0
}


class PackerError(Exception):
    pass


def unpack_tcp(buf, channels=None):
    while len(buf):
        size = struct.unpack('<I', buf[:4])[0]
        msg, buf = buf[4:size + 4], buf[size + 4:]
        yield unpack(msg, channels)


def pack_tcp(msgs, channels=None):
    buf = b''

    for msg in msgs:
        msg = pack(msg, channels)
        buf += struct.pack('<I', len(msg)) + msg

    return buf


def unpack(buf, channels=None):
    stream = BytesIO(buf)
    msg = Container()

    header = rtp(stream)
    payload = Container()

    if header['flags']['payload_type'] == RtpPayloadType.Control:
        data = struct.unpack('<BH', stream.read(3))
        payload['type'] = ChannelControlPayloadType(data[0])
        payload['connection_id'] = data[1]
    elif header.flags.payload_type == RtpPayloadType.ChannelControl:
        data = struct.unpack('<I', stream.read(4))
        payload['type'] = ChannelControlPayloadType(data[0])

        if payload['type'] == ChannelControlPayloadType.ChannelCreate:
            slen = struct.unpack('<H', stream.read(2))[0]
            payload['name'] = enum.ChannelClass(stream.read(slen).decode('utf8'))

        if payload['type'] in (ChannelControlPayloadType.ChannelCreate, ChannelControlPayloadType.ChannelClose):
            payload['flags'] = struct.unpack('<I', stream.read(4))[0]
        elif payload['type'] == ChannelControlPayloadType.ChannelOpen:
            slen = struct.unpack('<I', stream.read(4))[0]
            payload['flags'] = stream.read(slen)
    elif header['flags']['payload_type'] == RtpPayloadType.UDPHandshake:
        payload['unk'] = struct.unpack('<B', stream.read(1))[0]
    elif header['flags']['payload_type'] == RtpPayloadType.Streamer:
        if not channels:
            raise PackerError('No channels passed')

        channel_id = header['ssrc']['channel_id']
        if channel_id not in channels:
            raise PackerError('Unknown channel ID %d' % channel_id)

        channel = channels[channel_id]
        payload = streamer(header, channel.name, stream)

    msg['header'] = header
    msg['payload'] = payload
    return msg


def rtp(stream):
    flags = RTP_FLAGS.unpack(stream.read(2))
    data = struct.unpack('>HI2H', stream.read(10))

    r = Container()
    rflags = Container()
    rssrc = Container()

    rflags['version'] = flags[0]
    rflags['padding'] = flags[1]
    rflags['extension'] = flags[2]
    rflags['csrc_count'] = flags[3]
    rflags['marker'] = flags[4]
    rflags['payload_type'] = RtpPayloadType(flags[5])
    r['flags'] = rflags
    r['sequence_num'] = data[0]
    r['timestamp'] = data[1]
    rssrc['connection_id'] = data[2]
    rssrc['channel_id'] = data[3]
    r['ssrc'] = rssrc
    r['csrc_list'] = struct.unpack('>{}I'.format(flags[3]), stream.read(4 * flags[3]))

    return r


def streamer(header, channel, stream):
    streamer_header = Container()
    if header['ssrc']['connection_id'] == 0:
        # TCP
        data = struct.unpack('<4I', stream.read(16))
        streamer_header['streamer_version'] = data[0]
        streamer_header['sequence_num'] = data[1]
        streamer_header['prev_sequence_num'] = data[2]
        streamer_header['type'] = STREAMER_TYPE_MAP[channel](data[3])
    else:
        # UDP
        data = struct.unpack('<2I', stream.read(8))
        streamer_header['streamer_version'] = data[0]
        streamer_header['type'] = STREAMER_TYPE_MAP[channel](data[1])

    if header['ssrc']['connection_id'] == 0 and streamer_header['type'] == 0:
        pass
    else:
        stream.read(4)

    header['streamer'] = streamer_header
    payload = Container()
    payload_type = streamer_header['type']

    if channel == ChannelClass.Control:
        if payload_type == 0:
            payload = control(stream)

    elif channel == ChannelClass.Video:
        if payload_type == VideoPayloadType.Data:
            data = struct.unpack('<2IQ4I', stream.read(32))
            payload['flags'] = data[0]
            payload['frame_id'] = data[1]
            payload['timestamp'] = data[2]
            payload['total_size'] = data[3]
            payload['packet_count'] = data[4]
            payload['offset'] = data[5]
            payload['data'] = stream.read(data[6])
        elif payload_type == VideoPayloadType.ServerHandshake:
            data = struct.unpack('<4IQI', stream.read(28))
            payload['protocol_version'] = data[0]
            payload['width'] = data[1]
            payload['height'] = data[2]
            payload['fps'] = data[3]
            payload['reference_timestamp'] = data[4]
            formats = []
            for _ in range(data[5]):
                formats.append(video_fmt(stream))
            payload['formats'] = formats
        elif payload_type == VideoPayloadType.ClientHandshake:
            data = struct.unpack('<I', stream.read(4))
            payload['initial_frame_id'] = data[0]
            payload['requested_format'] = video_fmt(stream)
        elif payload_type == VideoPayloadType.Control:
            data = VIDEO_CONTROL_FLAGS.unpack(stream.read(4))
            flags = Container()
            flags['request_keyframe'] = data[0]
            flags['start_stream'] = data[1]
            flags['stop_stream'] = data[2]
            flags['queue_depth'] = data[3]
            flags['lost_frames'] = data[4]
            flags['last_displayed_frame'] = data[5]
            payload['flags'] = flags

            if flags['last_displayed_frame']:
                data = struct.unpack('<Iq', stream.read(12))
                payload['last_displayed_frame'] = Container()
                payload['last_displayed_frame']['frame_id'] = data[0]
                payload['last_displayed_frame']['timestamp'] = data[1]

            if flags['queue_depth']:
                payload['queue_depth'] = struct.unpack('<I', stream.read(4))

            if flags['lost_frames']:
                data = struct.unpack('<2I', stream.read(8))
                payload['lost_frames']['first'] = data[0]
                payload['lost_frames']['last'] = data[1]
    elif channel in (ChannelClass.Audio, ChannelClass.ChatAudio):
        if payload_type == AudioPayloadType.Data:
            data = struct.unpack('<2IQI', stream.read(20))
            payload['flags'] = data[0]
            payload['frame_id'] = data[1]
            payload['timestamp'] = data[2]
            payload['data'] = stream.read(data[3])
        elif payload_type == AudioPayloadType.ServerHandshake:
            data = struct.unpack('<IQI', stream.read(16))
            payload['protocol_version'] = data[0]
            payload['reference_timestamp'] = data[1]
            formats = []
            for _ in range(data[2]):
                formats.append(audio_fmt(stream))

            payload['formats'] = formats
        elif payload_type == AudioPayloadType.ClientHandshake:
            data = struct.unpack('<I', stream.read(4))
            payload['initial_frame_id'] = data[0]
            payload['requested_format'] = audio_fmt(stream)
        elif payload_type == AudioPayloadType.Control:
            data = AUDIO_CONTROL_FLAGS.unpack(stream.read(4))
            payload['flags'] = Container()
            payload['flags']['reinitialize'] = data[0]
            payload['flags']['start_stream'] = data[1]
            payload['flags']['stop_stream'] = data[2]
    elif channel in (ChannelClass.Input, ChannelClass.InputFeedback):
        if payload_type == InputPayloadType.Frame:
            data = struct.unpack('<I2Q', stream.read(20))
            payload['frame_id'] = data[0]
            payload['timestamp'] = data[1]
            payload['created_ts'] = data[2]

            buttons = Container()
            analog = Container()
            extension = Container()
            data = struct.unpack('>18B4H13B', stream.read(39))

            buttons['dpad_up'] = data[0]
            buttons['dpad_down'] = data[1]
            buttons['dpad_left'] = data[2]
            buttons['dpad_right'] = data[3]
            buttons['start'] = data[4]
            buttons['back'] = data[5]
            buttons['left_thumbstick'] = data[6]
            buttons['right_thumbstick'] = data[7]
            buttons['left_shoulder'] = data[8]
            buttons['right_shoulder'] = data[9]
            buttons['guide'] = data[10]
            buttons['unknown'] = data[11]
            buttons['a'] = data[12]
            buttons['b'] = data[13]
            buttons['x'] = data[14]
            buttons['y'] = data[15]
            analog['left_trigger'] = data[16]
            analog['right_trigger'] = data[17]
            analog['left_thumb_x'] = data[18]
            analog['left_thumb_y'] = data[19]
            analog['right_thumb_x'] = data[20]
            analog['right_thumb_y'] = data[21]
            analog['rumble_trigger_l'] = data[22]
            analog['rumble_trigger_r'] = data[23]
            analog['rumble_handle_l'] = data[24]
            analog['rumble_handle_r'] = data[25]
            extension['byte_6'] = data[26]
            extension['byte_7'] = data[27]
            extension['rumble_trigger_l2'] = data[28]
            extension['rumble_trigger_r2'] = data[29]
            extension['rumble_handle_l2'] = data[30]
            extension['rumble_handle_r2'] = data[31]
            extension['byte_12'] = data[32]
            extension['byte_13'] = data[33]
            extension['byte_14'] = data[34]

            payload['buttons'] = buttons
            payload['analog'] = analog
            payload['extension'] = extension
        elif payload_type == InputPayloadType.ServerHandshake:
            data = struct.unpack('<5I', stream.read(20))
            payload['protocol_version'] = data[0]
            payload['desktop_width'] = data[1]
            payload['desktop_height'] = data[2]
            payload['max_touches'] = data[3]
            payload['initial_frame_id'] = data[4]
        elif payload_type == InputPayloadType.ClientHandshake:
            data = struct.unpack('<IQ', stream.read(12))
            payload['max_touches'] = data[0]
            payload['reference_timestamp'] = data[1]
        elif payload_type == InputPayloadType.FrameAck:
            payload['acked_frame'] = struct.unpack('<I', stream.read(4))[0]

    return payload


def control(stream):
    payload = Container()
    ppayload = Container()

    data = struct.unpack('<I3H', stream.read(10))
    payload['prev_seq_dup'] = data[0]
    payload['unk1'] = data[1]
    payload['unk2'] = data[2]
    payload['opcode'] = ControlPayloadType(data[3])

    if payload.opcode == ControlPayloadType.SessionInit:
        ppayload['unk3'] = stream.read()
    elif payload.opcode == ControlPayloadType.SessionCreate:
        ppayload['guid'] = stream.read(16)
        ppayload['unk3'] = stream.read(struct.unpack('<I', stream.read(4))[0])
    elif payload.opcode == ControlPayloadType.SessionCreateResponse:
        ppayload['guid'] = stream.read(16)
    elif payload.opcode == ControlPayloadType.SessionDestroy:
        ppayload['unk3'] = struct.unpack('<f', stream.read(4))[0]
        ppayload['unk5'] = stream.read(struct.unpack('<I', stream.read(4))[0])
    elif payload.opcode == ControlPayloadType.VideoStatistics:
        data = struct.unpack('<6f', stream.read(24))
        ppayload['unk3'] = data[0]
        ppayload['unk4'] = data[1]
        ppayload['unk5'] = data[2]
        ppayload['unk6'] = data[3]
        ppayload['unk7'] = data[4]
        ppayload['unk8'] = data[5]
    elif payload.opcode == ControlPayloadType.RealtimeTelemetry:
        data = []
        for i in range(struct.unpack('<H', stream.read(2))[0]):
            p = struct.unpack('<HQ', stream.read(10))
            data.append(Container(
                key=p[0],
                value=p[1]
            ))
        ppayload['data'] = data
    elif payload.opcode == ControlPayloadType.ChangeVideoQuality:
        data = struct.unpack('<I5f', stream.read(24))
        ppayload['unk3'] = data[0]
        ppayload['unk4'] = data[1]
        ppayload['unk5'] = data[2]
        ppayload['unk6'] = data[3]
        ppayload['unk7'] = data[4]
        ppayload['unk8'] = data[5]
    elif payload.opcode == ControlPayloadType.InitiateNetworkTest:
        ppayload['guid'] = stream.read(16)
    elif payload.opcode == ControlPayloadType.NetworkInformation:
        ppayload['guid'] = stream.read(16)
        data = struct.unpack('<QBf', stream.read(13))
        ppayload['unk4'] = data[0]
        ppayload['unk5'] = data[1]
        ppayload['unk6'] = data[2]
    elif payload.opcode == ControlPayloadType.NetworkTestResponse:
        ppayload['guid'] = stream.read(16)
        data = struct.unpack('<5f2Qf', stream.read(40))
        ppayload['unk3'] = data[0]
        ppayload['unk4'] = data[1]
        ppayload['unk5'] = data[2]
        ppayload['unk6'] = data[3]
        ppayload['unk7'] = data[4]
        ppayload['unk8'] = data[5]
        ppayload['unk9'] = data[6]
        ppayload['unk10'] = data[7]
    elif payload.opcode == ControlPayloadType.ControllerEvent:
        data = struct.unpack('<2B')
        ppayload['event'] = ControllerEvent(data[0])
        ppayload['controller_num'] = data[1]

    payload['payload'] = ppayload
    return payload


def video_fmt(stream):
    data = struct.unpack('<4I', stream.read(16))
    fmt = Container()
    fmt['fps'] = data[0]
    fmt['width'] = data[1]
    fmt['height'] = data[2]
    fmt['codec'] = enum.VideoCodec(data[3])
    fmt['rgb'] = Container()
    if fmt['codec'] == enum.VideoCodec.RGB:
        data = struct.unpack('<2I3Q', stream.read(32))
        fmt['rgb']['bpp'] = data[0]
        fmt['rgb']['bytes'] = data[1]
        fmt['rgb']['red_mask'] = data[2]
        fmt['rgb']['green_mask'] = data[3]
        fmt['rgb']['blue_mask'] = data[4]

    return fmt


def audio_fmt(stream):
    data = struct.unpack('<3I', stream.read(12))
    fmt = Container()
    fmt['channels'] = data[0]
    fmt['sample_rate'] = data[1]
    fmt['codec'] = enum.AudioCodec(data[2])
    fmt['pcm'] = Container()
    if fmt['codec'] == enum.AudioCodec.PCM:
        data = struct.unpack('<2I', stream.read(8))
        fmt['pcm']['bit_depth'] = data[0]
        fmt['pcm']['type'] = data[1]

    return fmt
