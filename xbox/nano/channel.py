import time
import random
import logging
from collections import deque
from datetime import datetime

from xbox.nano import factory
from xbox.nano.packet import audio
from xbox.nano.enum import ChannelClass, VideoPayloadType, AudioPayloadType, \
    InputPayloadType, ControlPayloadType, ControllerEvent, VideoQuality

log = logging.getLogger(__name__)


class Channel(object):
    def __init__(self, client, protocol, channel_id, name, flags):
        self.client = client
        self.protocol = protocol

        self.id = channel_id
        self.name = name
        self.flags = flags
        self.open = False

        self._sequence_num = 0
        self._frame_id = 0
        self._ref_timestamp = None

    def __repr__(self):
        return '<{:s} id={:d} class={:s} flags=0x{:08x} opened={:}>'.format(
            self.__class__.__name__, self.id, self.name, self.flags, self.open
        )

    @property
    def sequence_num(self):
        return self._sequence_num

    @property
    def next_sequence_num(self):
        self._sequence_num += 1
        return self._sequence_num

    @property
    def reference_timestamp(self):
        return self._ref_timestamp

    @reference_timestamp.setter
    def reference_timestamp(self, val):
        self._ref_timestamp = val
        log.debug("%s - Set Reference timestamp: %s", self.name, self._ref_timestamp)

    def generate_reference_timestamp(self):
        self.reference_timestamp = datetime.utcnow()
        return self.reference_timestamp

    @property
    def frame_id(self):
        return self._frame_id

    @property
    def next_frame_id(self):
        self._frame_id += 1
        return self._frame_id

    @frame_id.setter
    def frame_id(self, val):
        log.debug("%s - Initial Frame Id: %i", self.name, val)
        self._frame_id = val

    def generate_initial_frame_id(self):
        self._frame_id = random.randint(0, 500)
        return self._frame_id

    def send_tcp_streamer(self, payload_type, payload):
        prev_seq = self.sequence_num
        msg = factory.streamer_tcp(
            self.next_sequence_num, prev_seq, payload_type, payload,
            channel_id=self.id
        )

        self.protocol.control_protocol.send_message(msg)

    def send_udp_streamer(self, payload_type, payload):
        msg = factory.streamer_udp(
            payload_type, payload,
            connection_id=self.protocol.connection_id, channel_id=self.id,
            sequence_num=self.next_sequence_num
        )

        self.protocol.streamer_protocol.send_message(msg)

    def on_message(self, msg):
        raise NotImplementedError()

    def on_open(self, flags):
        raise NotImplementedError()

    def on_close(self, flags):
        raise NotImplementedError()


class VideoChannel(Channel):
    def __init__(self, *args, **kwargs):
        super(VideoChannel, self).__init__(*args, **kwargs)
        self._frame_buf = {}
        self._frame_expiry_time = 3.0
        self._render_queue = deque()

    def on_message(self, msg):
        if VideoPayloadType.Data == msg.header.streamer.type:
            self.on_data(msg)
        elif VideoPayloadType.ServerHandshake == msg.header.streamer.type:
            self.on_server_handshake(msg)
        else:
            log.warning("Unknown message received on VideoChannel", extra={'_msg': msg})

    def on_open(self, flags):
        self.protocol.channel_open(flags, self.id)

    def on_close(self, flags):
        raise NotImplementedError()

    def client_handshake(self, video_format):
        payload = factory.video.client_handshake(
            initial_frame_id=self.generate_initial_frame_id(),
            requested_format=video_format
        )
        self.client.set_video_format(video_format)
        self.send_tcp_streamer(VideoPayloadType.ClientHandshake, payload)

    def on_server_handshake(self, msg):
        payload = msg.payload
        log.debug("VideoChannel server handshake", extra={'_msg': msg})
        self.reference_timestamp = payload.reference_timestamp
        self.client_handshake(payload.formats[0])
        # You could set initial video format here
        # self.protocol.get_channel(ChannelClass.Control).change_video_quality(VideoQuality.Middle)
        self.control()

    def on_data(self, msg):
        flags = msg.payload.flags
        frame_id = msg.payload.frame_id
        timestamp = msg.payload.timestamp
        packet_count = msg.payload.packet_count

        if packet_count == 1:
            self._render_queue.append((
                frame_id, flags, timestamp, msg.payload.data
            ))
        else:
            if frame_id not in self._frame_buf:
                # msg list, current count, packet count
                frame_buf = [[msg], 1, packet_count, time.time()]
                self._frame_buf[frame_id] = frame_buf
            else:
                frame_buf = self._frame_buf[frame_id]
                frame_buf[0].append(msg)
                frame_buf[1] += 1

            # current count == packet count
            if frame_buf[1] == frame_buf[2]:
                data_buf = frame_buf[0]
                data_buf.sort(key=lambda x: x.payload.offset)
                frame = b''.join([packet.payload.data for packet in data_buf])

                self.client.render_video(frame)
                del self._frame_buf[frame_id]

        # Discard frames older than self._frame_expiry_time
        self._frame_buf = {k: v for (k, v) in self._frame_buf.items()
                           if (time.time() - v[3]) < self._frame_expiry_time}

    def control(self, start_stream=True):
        # TODO
        if start_stream:
            payload = factory.video.control(
                request_keyframe=True, start_stream=True
            )
        else:
            payload = factory.video.control(stop_stream=True)

        self.send_tcp_streamer(VideoPayloadType.Control, payload)


class AudioChannel(Channel):
    def on_message(self, msg):
        if AudioPayloadType.Data == msg.header.streamer.type:
            self.on_data(msg)
        elif AudioPayloadType.ServerHandshake == msg.header.streamer.type:
            self.on_server_handshake(msg)
        else:
            log.warning("Unknown message received on AudioChannel", extra={'_msg': msg})

    def on_open(self, flags):
        self.protocol.channel_open(flags, self.id)

    def on_close(self, flags):
        self.client.close()

    def client_handshake(self, audio_format):
        payload = factory.audio.client_handshake(
            initial_frame_id=self.generate_initial_frame_id(),
            requested_format=audio_format
        )
        self.client.set_audio_format(audio_format)
        self.send_tcp_streamer(AudioPayloadType.ClientHandshake, payload)

    def on_server_handshake(self, msg):
        payload = msg.payload
        log.debug("AudioChannel server handshake", extra={'_msg': msg})
        self.reference_timestamp = payload.reference_timestamp
        self.client_handshake(payload.formats[0])
        self.control()

    def on_data(self, msg):
        # print('AudioChannel:on_data ', msg)
        self.client.render_audio(msg.payload.data)

    def control(self):
        payload = factory.audio.control(
            reinitialize=False, start_stream=True, stop_stream=False
        )
        self.send_tcp_streamer(AudioPayloadType.Control, payload)


class ChatAudioChannel(Channel):
    """
    This one is special
    1. Client sends ServerHandshake initially
    2. Host responds with ClientHandshake
    """
    def on_message(self, msg):
        if AudioPayloadType.ClientHandshake == msg.header.streamer.type:
            self.on_client_handshake(msg)
        elif AudioPayloadType.Control == msg.header.streamer.type:
            self.on_control(msg)
        else:
            log.warning("Unknown message received on ChatAudioChannel",
                        extra={'_msg': msg})

    def on_open(self, flags):
        self.protocol.channel_open(flags, self.id)

    def on_close(self, flags):
        self.client.close()

    def on_client_handshake(self, msg):
        log.debug("ChatAudioChannel client handshake", extra={'_msg': msg})
        raise NotImplementedError("We should configure audio input parameters / encoder here")

    def server_handshake(self):
        # 1 Channel, Samplerate: 24000, Codec: Opus
        formats = [audio.fmt(1, 24000, 0)]
        payload = factory.audio.server_handshake(
            protocol_version=4,
            reference_timestamp=self.generate_reference_timestamp(),
            formats=formats
        )
        self.send_tcp_streamer(AudioPayloadType.ServerHandshake, payload)

    def on_control(self, msg):
        raise NotImplementedError("We should start streaming ChatAudio frames here")

    def data(self, data):
        ts = int(time.time())
        payload = factory.audio.data(
            flags=4, frame_id=0, timestamp=ts, data=data
        )
        self.send_udp_streamer(AudioPayloadType.Data, payload)


class InputChannel(Channel):
    def get_input_timestamp_from_dt(self, datetime_obj):
        """
        Nanoseconds (1/1000000)s
        """
        delta = (datetime_obj - self.reference_timestamp)
        return int(delta.total_seconds() * 100000)

    def get_input_timestamp_now(self):
        return self.get_input_timestamp_from_dt(datetime.utcnow())

    def on_message(self, msg):
        if InputPayloadType.ServerHandshake == msg.header.streamer.type:
            self.on_server_handshake(msg)
        elif InputPayloadType.FrameAck == msg.header.streamer.type:
            self.on_frame_ack(msg)
        else:
            log.warning("Unknown message received on InputChannel", extra={'_msg': msg})

    def on_open(self, flags):
        self.protocol.channel_open(flags, self.id)

    def on_close(self, flags):
        pass

    def client_handshake(self, max_touches=10):
        payload = factory.input.client_handshake(
            max_touches=max_touches,
            reference_timestamp=self.generate_reference_timestamp()
        )
        self.send_tcp_streamer(InputPayloadType.ClientHandshake, payload)

    def on_server_handshake(self, msg):
        log.debug("InputChannel server handshake", extra={'_msg': msg})
        self.frame_id = msg.payload.initial_frame_id
        self.client_handshake()

    def on_frame_ack(self, msg):
        log.debug("Acked InputFrame: %s", msg.payload.acked_frame)

    def send_frame(self, input_frame, created_dt):
        input_frame = input_frame(
            frame_id=self.next_frame_id,
            timestamp=self.get_input_timestamp_now(),
            created_ts=self.get_input_timestamp_from_dt(created_dt)
        )
        log.debug("Sending Input Frame msg: %s", input_frame)
        self.send_udp_streamer(InputPayloadType.Frame, input_frame)


class InputFeedbackChannel(Channel):
    """
    This one is special
    1. Client sends ServerHandshake initially
    2. Host responds with ClientHandshake
    """
    def on_message(self, msg):
        if InputPayloadType.ClientHandshake == msg.header.streamer.type:
            self.on_client_handshake(msg)
        elif InputPayloadType.Frame == msg.header.streamer.type:
            self.on_frame(msg)
        else:
            log.warning("Unknown message received on InputFeedbackChannel", extra={'_msg': msg})

    def on_open(self, flags):
        self.protocol.channel_open(flags, self.id)
        self.server_handshake()

    def on_close(self, flags):
        raise NotImplementedError()

    def on_client_handshake(self, msg):
        log.debug("InputFeedbackChannel ClientHandshake", extra={'_msg': msg})

    def on_frame(self, msg):
        log.debug("InputFeedbackChannel Frame", extra={'_msg': msg})
        # raise NotImplementedError()

    def server_handshake(self):
        frame_id = random.randint(0, 500)
        # TODO: Do not hardcode desktop width/height
        payload = factory.input.server_handshake(
            protocol_version=3,
            desktop_width=1280,
            desktop_height=720,
            max_touches=0,
            initial_frame_id=frame_id
        )
        self.send_tcp_streamer(InputPayloadType.ServerHandshake, payload)


class ControlChannel(Channel):
    def on_message(self, msg):
        opcode = msg.payload.opcode
        if ControlPayloadType.RealtimeTelemetry == opcode:
            # Mute telemetry...
            pass
        else:
            log.warning("Unknown message received on ControlChannel", extra={'_msg': msg})

    def on_open(self, flags):
        self.protocol.channel_open(flags, self.id)
        # self.client.on_control_channel_established()

    def on_close(self, flags):
        raise NotImplementedError()

    def client_handshake(self):
        raise NotImplementedError()

    def server_handshake(self):
        raise NotImplementedError()

    def _send_control_msg(self, opcode, payload):
        msg = factory.control.control_header(
            prev_seq_dup=self.sequence_num,
            unk1=1,
            unk2=1406,
            opcode=opcode,
            payload=payload.container
        )
        self.send_tcp_streamer(0, msg)

    def change_video_quality(self, quality):
        payload = factory.control.change_video_quality(
            quality[0], quality[1], quality[2],
            quality[3], quality[4], quality[5]
        )
        log.debug("Sending Change Video Quality msg: %s", payload)
        self._send_control_msg(ControlPayloadType.ChangeVideoQuality, payload)

    def controller_added(self, num=0):
        payload = factory.control.controller_event(ControllerEvent.Added, num)
        log.debug("Sending Controller added msg: %s", payload)
        self._send_control_msg(ControlPayloadType.ControllerEvent, payload)

    def controller_removed(self, num=0):
        payload = factory.control.controller_event(
            ControllerEvent.Removed, num
        )
        log.debug("Sending Controller removed msg: %s", payload)
        self._send_control_msg(ControlPayloadType.ControllerEvent, payload)


CHANNEL_CLASS_MAP = {
    ChannelClass.Video: VideoChannel,
    ChannelClass.Audio: AudioChannel,
    ChannelClass.ChatAudio: ChatAudioChannel,
    ChannelClass.Input: InputChannel,
    ChannelClass.InputFeedback: InputFeedbackChannel,
    ChannelClass.Control: ControlChannel,
}
