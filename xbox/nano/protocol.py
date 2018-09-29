import time
import random
import logging

import gevent
import gevent.event
from gevent import socket
from gevent.server import DatagramServer

from xbox.sg.utils.events import Event

from xbox.nano import factory, packer
from xbox.nano.enum import RtpPayloadType, ChannelControlPayloadType
from xbox.nano.channel import CHANNEL_CLASS_MAP

log = logging.getLogger(__name__)


class NanoProtocolError(Exception):
    pass


class NanoProtocol(object):
    """
    Client sends ChannelClientHandshake with generated connection id
    Server responds with ChannelServerHandshake with connection id

    UDP protocol sends HandShakeUDP 0x1 with connection ID in RTP header

    Server sends ChannelCreates and ChannelOpens
    Client responds with ChannelOpens (copying possible flags)
    """
    def __init__(self, client, address, session_id, tcp_port, udp_port):
        self.client = client
        self.session_id = session_id

        self.channels = {}
        self.connection_id = 0
        self.connected = gevent.event.Event()

        self.control_protocol = ControlProtocol(address, tcp_port, self)
        self.streamer_protocol = StreamerProtocol(address, udp_port, self)

        # TODO: pull this more into NanoProtocol if it's a bottleneck?
        self.control_protocol.on_message += self._on_control_message
        self.streamer_protocol.on_message += self._on_streamer_message

    def start(self):
        self.control_protocol.start()
        self.streamer_protocol.start()
        self.client.open(self)

    def stop(self):
        # TODO: close channels and stuff?
        self.control_protocol.stop()
        self.streamer_protocol.stop()

    def connect(self, timeout=10):
        with gevent.Timeout(timeout, NanoProtocolError):
            self.channel_control_handshake()
            self.connected.wait()

            self.udp_handshake()
            while not self.streamer_protocol.connected.wait(0.2):
                self.udp_handshake()

    def get_channel(self, channel_class):
        """
        Get channel instance by channel class identifier

        Args:
            channel_class (:class:`.ChannelClass`): Enum member of
                :class:`.ChannelClass`

        Returns:
            :obj:`.Channel`: Instance of channel
        """
        _class = CHANNEL_CLASS_MAP[channel_class]
        for channel in self.channels.values():
            if isinstance(channel, _class):
                return channel

    def _on_control_message(self, msg):
        payload_type = msg.header.flags.payload_type
        channel_id = msg.header.ssrc.channel_id

        if payload_type == RtpPayloadType.Control and \
                msg.payload.type == ChannelControlPayloadType.ServerHandshake:
            self.connection_id = msg.payload.connection_id
            self.connected.set()

        elif payload_type == RtpPayloadType.ChannelControl:
            if msg.payload.type == ChannelControlPayloadType.ChannelCreate:
                channel_name = msg.payload.name

                if channel_name not in CHANNEL_CLASS_MAP:
                    raise NanoProtocolError(
                        "Unsupported channel: %s", channel_name
                    )

                channel = CHANNEL_CLASS_MAP[channel_name](
                    self.client, self,
                    channel_id, channel_name, msg.payload.flags
                )

                self.channels[channel_id] = channel
                log.info("Channel created: %s", channel)

            elif channel_id not in self.channels:
                raise NanoProtocolError("Unknown channel: %d", channel_id)

            elif msg.payload.type == ChannelControlPayloadType.ChannelOpen:
                channel = self.channels[channel_id]
                channel.open = True
                channel.on_open(msg.payload.flags)

                log.info("Channel opened with flags %s: %s",
                         msg.payload.flags, channel)

            elif msg.payload.type == ChannelControlPayloadType.ChannelClose:
                channel = self.channels[channel_id]
                channel.open = False
                channel.on_close(msg.payload.flags)

                log.info("Channel closed: %s", channel)

        elif payload_type == RtpPayloadType.Streamer:
            self.channels[channel_id].on_message(msg)

        else:
            log.warning("Unknown payload type", extra={'_msg': msg})

    def _on_streamer_message(self, msg):
        channel_id = msg.header.ssrc.channel_id

        if channel_id not in self.channels:
            log.warning("Unknown channel id: %d", channel_id)
            # TODO: what to do here?
            log.warning(msg)
            return

        self.channels[channel_id].on_message(msg)

    def channel_control_handshake(self, connection_id=None):
        if not connection_id:
            connection_id = random.randint(50000, 60000)

        msg = factory.channel.control_handshake(connection_id)
        self.control_protocol.send_message(msg)

    def channel_create(self, name, flags, channel_id):
        msg = factory.channel.create(name, flags, channel_id)
        self.control_protocol.send_message(msg)

    def channel_open(self, flags, channel_id):
        msg = factory.channel.open(flags, channel_id)
        self.control_protocol.send_message(msg)

    def channel_close(self, flags, channel_id):
        msg = factory.channel.close(flags, channel_id)
        self.control_protocol.send_message(msg)

    def udp_handshake(self):
        msg = factory.udp_handshake(self.connection_id)
        self.streamer_protocol.send_message(msg)


class ControlProtocolError(Exception):
    pass


class ControlProtocol(object):
    BUFFER_SIZE = 4096

    def __init__(self, address, port, nano):
        self.host = (address, port)
        self._nano = nano  # Do we want this? Circular reference..
        self._q = []
        self._socket = None
        self._recv_thread = None

        self.on_message = Event()

    def start(self):
        self._socket = socket.create_connection(self.host)
        self._recv_thread = gevent.spawn(self._recv)

    def stop(self):
        self._socket.close()
        gevent.kill(self._recv_thread)

    def handle(self, data):
        try:
            for msg in packer.unpack_tcp(data, self._nano.channels):
                self.on_message(msg)
        except Exception as e:
            log.exception("Exception in ControlProtocol message handler")

    def _recv(self):
        while 1:
            socket.wait_read(self._socket.fileno())
            data = self._socket.recv(self.BUFFER_SIZE)
            self.handle(data)

    def _send(self, msgs):
        data = packer.pack_tcp(msgs, self._nano.channels)

        if not data:
            raise ControlProtocolError('No data')

        self._socket.send(data)

    def queue(self, msg):
        self._q.append(msg)

    def flush(self):
        self._send(self._q)
        self._q = []

    def send_message(self, msg):
        self.queue(msg)
        self.flush()


class StreamerProtocolError(Exception):
    pass


class StreamerProtocol(DatagramServer):
    def __init__(self, address, port, nano):
        self.host = (address, port)
        self.connected = gevent.event.Event()
        self._nano = nano  # Do we want this? Circular reference..

        self.on_message = Event()

        super(DatagramServer, self).__init__(('*:0'))

    def stop(self, *args, **kwargs):
        super(DatagramServer, self).stop(*args, **kwargs)

    def handle(self, data, addr):
        if not self.connected.is_set():
            self.connected.set()

        try:
            msg = packer.unpack(data, self._nano.channels)
            msg(_incoming_ts=time.time())
            self.on_message(msg)
        except Exception as e:
            log.exception("Exception in StreamerProtocol message handler")

    def send_message(self, msg):
        data = packer.pack(msg)

        if not data:
            raise StreamerProtocolError('No data')

        self.socket.sendto(data, self.host)
