import logging
from xbox.sg.manager import Manager
from xbox.sg.enum import ServiceChannel
from xbox.sg.utils.events import Event

from xbox.nano.packet import json
from xbox.nano.protocol import NanoProtocol
from xbox.nano.enum import GameStreamState, BroadcastMessageType

log = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "audioFecType": "0",
    "audioSyncPolicy": "1",
    "audioSyncMaxLatency": "170",
    "audioSyncDesiredLatency": "40",
    "audioSyncMinLatency": "10",
    "audioSyncCompressLatency": "100",
    "audioSyncCompressFactor": "0.99",
    "audioSyncLengthenFactor": "1.01",
    "audioBufferLengthHns": "10000000",

    "enableOpusChatAudio": "true",
    "enableDynamicBitrate": "false",
    "enableAudioChat": "true",
    "enableVideoFrameAcks": "false",
    "enableOpusAudio": "false",

    "dynamicBitrateUpdateMs": "5000",
    "dynamicBitrateScaleFactor": "1",

    "inputReadsPerSecond": "120",

    "videoFecType": "0",
    "videoFecLevel": "3",
    "videoMaximumWidth": "1280",
    "videoMaximumHeight": "720",
    "videoMaximumFrameRate": "60",
    "videoPacketUtilization": "0",
    "videoPacketDefragTimeoutMs": "16",
    "sendKeyframesOverTCP": "false",

    "udpSubBurstGroups": "5",
    "udpBurstDurationMs": "11",
    "udpMaxSendPacketsInWinsock": "250",

    "urcpType": "0",
    "urcpFixedRate": "-1",
    "urcpMaximumRate": "10000000",
    "urcpMinimumRate": "256000",
    "urcpMaximumWindow": "1310720",
    "urcpKeepAliveTimeoutMs": "0"
}


class NanoManagerError(Exception):
    pass


class NanoManager(Manager):
    __namespace__ = 'nano'
    PROTOCOL_MAJOR_VERSION = 6
    PROTOCOL_MINOR_VERSION = 0

    def __init__(self, console):
        super(NanoManager, self).__init__(
            console, ServiceChannel.SystemBroadcast
        )

        self.client = None
        self._protocol = None
        self._connected = False
        self._current_state = GameStreamState.Unknown

        self.on_gamestream_error = Event()

        self._stream_states = {}
        self._stream_enabled = None
        self._stream_error = None
        self._stream_telemetry = None
        self._stream_previewstatus = None

    async def start_stream(self, config: dict = DEFAULT_CONFIG):
        msg = json.BroadcastStartStream(
            type=BroadcastMessageType.StartGameStream,
            reQueryPreviewStatus=True,
            configuration=config
        )
        await self._send_json(msg.dict())

    async def stop_stream(self):
        if self._connected and self._protocol:
            self._protocol.disconnect()
            self._protocol.stop()
            self._connected = False

        msg = json.BroadcastStopStream(
            type=BroadcastMessageType.StopGameStream
        )
        await self._send_json(msg.dict())

    async def start_gamestream(self, client):
        if not self.streaming:
            raise NanoManagerError('start_gamestream: Connection params not ready')

        self._protocol = NanoProtocol(
            client, self.console.address, self.session_id, self.tcp_port, self.udp_port
        )
        await self._protocol.start()
        await self._protocol.connect()
        self._connected = True

    def _on_json(self, data, service_channel):
        msg = json.parse(data)

        # Convert integer representation to BroadcastMessageType enum
        msg_type = BroadcastMessageType(msg.type)

        if msg_type == BroadcastMessageType.GameStreamState:
            # Convert integer representation to GameStreamState enum
            msg_state = GameStreamState(msg.state)
            if msg_state in [GameStreamState.Stopped, GameStreamState.Unknown]:
                # Clear previously received states
                self._stream_states = {}

            self._stream_states[msg_state] = msg
            self._current_state = msg_state
        elif msg_type == BroadcastMessageType.GameStreamEnabled:
            self._stream_enabled = msg
        elif msg_type == BroadcastMessageType.PreviewStatus:
            self._stream_previewstatus = msg
        elif msg_type == BroadcastMessageType.Telemetry:
            self._stream_telemetry = msg
        elif msg_type == BroadcastMessageType.GameStreamError:
            self._stream_error = msg
            self.on_gamestream_error(msg)
        elif msg_type in [BroadcastMessageType.StartGameStream,
                          BroadcastMessageType.StopGameStream]:
            raise NanoManagerError('{0} received on client side'.format(msg_type.name))

    @property
    def client_major_version(self):
        return self.PROTOCOL_MAJOR_VERSION

    @property
    def client_minor_version(self):
        return self.PROTOCOL_MINOR_VERSION

    @property
    def stream_connected(self):
        return self._connected

    @property
    def stream_state(self):
        return self._current_state

    @property
    def streaming(self):
        return GameStreamState.Started in self._stream_states

    @property
    def stream_enabled(self):
        if self._stream_enabled:
            return self._stream_enabled.enabled

    @property
    def stream_can_be_enabled(self):
        if self._stream_enabled:
            return self._stream_enabled.canBeEnabled

    @property
    def server_major_version(self):
        if self._stream_enabled:
            return self._stream_enabled.majorProtocolVersion

    @property
    def server_minor_version(self):
        if self._stream_enabled:
            return self._stream_enabled.minorProtocolVersion

    @property
    def wireless(self):
        if GameStreamState.Started in self._stream_states:
            return self._stream_states[GameStreamState.Started].isWirelessConnection

    @property
    def transmit_linkspeed(self):
        if GameStreamState.Started in self._stream_states:
            return self._stream_states[GameStreamState.Started].transmitLinkSpeed

    @property
    def wireless_channel(self):
        if GameStreamState.Started in self._stream_states:
            return self._stream_states[GameStreamState.Started].wirelessChannel

    @property
    def session_id(self):
        if GameStreamState.Initializing in self._stream_states:
            return self._stream_states[GameStreamState.Initializing].sessionId

    @property
    def tcp_port(self):
        if GameStreamState.Initializing in self._stream_states:
            return self._stream_states[GameStreamState.Initializing].tcpPort

    @property
    def udp_port(self):
        if GameStreamState.Initializing in self._stream_states:
            return self._stream_states[GameStreamState.Initializing].udpPort
