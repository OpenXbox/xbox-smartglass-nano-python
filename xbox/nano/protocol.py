import time
import random
import logging
from typing import Optional, Tuple, List

import asyncio
from asyncio.streams import StreamReader, StreamWriter
from asyncio.transports import DatagramTransport
from asyncio.protocols import DatagramProtocol

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
    def __init__(self, client, address: str, session_id, tcp_port: int, udp_port: int):
        self.loop = asyncio.get_running_loop()

        self.client = client
        self.session_id = session_id

        self.remote_addr = address
        self.tcp_port = tcp_port
        self.udp_port = udp_port

        self.channels = {}
        self.connection_id = 0
        self.connected = asyncio.Future()

        self.control_protocol: ControlProtocol = ControlProtocol(address, tcp_port, self)
        self.streamer_transport: Optional[DatagramTransport] = None
        self.streamer_protocol: Optional[StreamerProtocol] = None

    async def start(self):
        # Initialize TCP socket
        self.control_protocol.on_message += self._on_control_message
        await self.control_protocol.start()

        # Initialize UDP socket
        self.streamer_transport, self.streamer_protocol = await self.loop.create_datagram_endpoint(
            lambda: StreamerProtocol(self),
            remote_addr=(self.remote_addr, self.udp_port)
        )
        self.streamer_protocol.on_message += self._on_streamer_message
        
        self.client.open(self)

    async def stop(self):
        self.control_protocol.on_message -= self._on_control_message
        self.streamer_protocol.on_message -= self._on_streamer_message

        # TODO: close channels and stuff?
        await self.control_protocol.stop()
        self.streamer_transport.close()

    async def connect(self, timeout=10):
        self.channel_control_handshake()

        async def udp_handshake_loop():
            while not self.streamer_protocol.connected.done():
                self.udp_handshake()
                await asyncio.sleep(0.5)
        
        asyncio.create_task(udp_handshake_loop())

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
            self.connected.set_result(True)

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

    def __init__(self, address: str, port: int, nano: NanoProtocol):
        self.host: Tuple[str, int] = (address, port)
        self._nano = nano  # Do we want this? Circular reference..
        self._q = []
        self._reader: Optional[StreamReader] = None
        self._writer: Optional[StreamWriter] = None
        self._recv_task: Optional[asyncio.Task] = None

        self.on_message = Event()

    async def start(self):
        address, port = self.host
        self._reader, self._writer = await asyncio.open_connection(address, port)
        self._recv_task = asyncio.create_task(self._recv())

    async def stop(self):
        if self._recv_task:
            self._recv_task.cancel()
            try:
                await self._recv_task
            except asyncio.CancelledError:
                log.warning('ControlProtocol: Cancelled recv task')

        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()

    async def handle(self, data):
        try:
            for msg in packer.unpack_tcp(data, self._nano.channels):
                self.on_message(msg)
        except Exception as e:
            log.exception("Exception in ControlProtocol message handler")

    async def _recv(self):
        while True:
            data = await self._reader.read(self.BUFFER_SIZE)
            await self.handle(data)

    def _send(self, msgs):
        data = packer.pack_tcp(msgs, self._nano.channels)

        if not data:
            raise ControlProtocolError('No data')

        self._writer.write(data)
        # await self._writer.drain()

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


class StreamerProtocol(object):
    def __init__(self, nano: NanoProtocol):
        self._nano: NanoProtocol = nano  # Do we want this? Circular reference..

        self.connected = asyncio.Future()
        self.transport: Optional[DatagramTransport] = None

        self.on_message = Event()

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        if not self.connected.done():
            self.connected.set_result(True)

        try:
            msg = packer.unpack(data, self._nano.channels)
            msg(_incoming_ts=time.time())
            self.on_message(msg)
        except Exception as e:
            log.exception("Exception in StreamerProtocol message handler")

    def error_received(self, exc):
        print('Error received:', exc)

    def connection_lost(self, exc):
        print("Connection closed")

    def send_message(self, msg):
        data = packer.pack(msg)

        if not data:
            raise StreamerProtocolError('No data')

        self.transport.sendto(data)
