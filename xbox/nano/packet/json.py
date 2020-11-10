from typing import Union
from pydantic import BaseModel
from xbox.nano.enum import BroadcastMessageType, GameStreamState


class BroadcastJsonError(Exception):
    pass


class BaseBroadcastMessage(BaseModel):
    type: BroadcastMessageType

    class Config:
        use_enum_values = True


class BroadcastStreamEnabled(BaseBroadcastMessage):
    enabled: bool
    canBeEnabled: bool
    majorProtocolVersion: int
    minorProtocolVersion: int


class BroadcastPreviewStatus(BaseBroadcastMessage):
    isPublicPreview: bool
    isInternalPreview: bool


class GamestreamConfiguration(BaseModel):
    audioFecType: str
    audioSyncPolicy: str
    audioSyncMaxLatency: str
    audioSyncDesiredLatency: str
    audioSyncMinLatency: str
    audioSyncCompressLatency: str
    audioSyncCompressFactor: str
    audioSyncLengthenFactor: str
    audioBufferLengthHns: str

    enableOpusChatAudio: str
    enableDynamicBitrate: str
    enableAudioChat: str
    enableVideoFrameAcks: str
    enableOpusAudio: str

    dynamicBitrateUpdateMs: str
    dynamicBitrateScaleFactor: str

    inputReadsPerSecond: str

    videoFecType: str
    videoFecLevel: str
    videoMaximumWidth: str
    videoMaximumHeight: str
    videoMaximumFrameRate: str
    videoPacketUtilization: str
    videoPacketDefragTimeoutMs: str
    sendKeyframesOverTCP: str

    udpSubBurstGroups: str
    udpBurstDurationMs: str
    udpMaxSendPacketsInWinsock: str

    urcpType: str
    urcpFixedRate: str
    urcpMaximumRate: str
    urcpMinimumRate: str
    urcpMaximumWindow: str
    urcpKeepAliveTimeoutMs: str


class BroadcastStartStream(BaseBroadcastMessage):
    configuration: GamestreamConfiguration
    reQueryPreviewStatus: bool = False


class BroadcastStopStream(BaseBroadcastMessage):
    pass


class BroadcastError(BaseBroadcastMessage):
    errorType: int
    errorValue: int


class BroadcastTelemetry(BaseBroadcastMessage):
    pass


class BaseBroadcastStateMessage(BaseBroadcastMessage):
    state: GameStreamState
    sessionId: str


class BroadcastStateUnknown(BaseBroadcastStateMessage):
    pass


class BroadcastStateInitializing(BaseBroadcastStateMessage):
    udpPort: int
    tcpPort: int


class BroadcastStateStarted(BaseBroadcastStateMessage):
    isWirelessConnection: bool
    wirelessChannel: int
    transmitLinkSpeed: int


class BroadcastStateStopped(BaseBroadcastStateMessage):
    pass


class BroadcastStatePaused(BaseBroadcastStateMessage):
    pass


TYPE_MAP = {
    BroadcastMessageType.StartGameStream: BroadcastStartStream,
    BroadcastMessageType.StopGameStream: BroadcastStopStream,
    BroadcastMessageType.GameStreamState: BaseBroadcastStateMessage,
    BroadcastMessageType.GameStreamEnabled: BroadcastStreamEnabled,
    BroadcastMessageType.GameStreamError: BroadcastError,
    BroadcastMessageType.Telemetry: BroadcastTelemetry,
    BroadcastMessageType.PreviewStatus: BroadcastPreviewStatus
}

STATE_MAP = {
    GameStreamState.Unknown: BroadcastStateUnknown,
    GameStreamState.Initializing: BroadcastStateInitializing,
    GameStreamState.Started: BroadcastStateStarted,
    GameStreamState.Stopped: BroadcastStateStopped,
    GameStreamState.Paused: BroadcastStatePaused
}


def parse(
    data: dict
) -> Union[
        BroadcastStartStream, BroadcastStopStream, BroadcastStreamEnabled,
        BroadcastError, BroadcastTelemetry, BroadcastPreviewStatus,
        BroadcastStateUnknown, BroadcastStateInitializing, BroadcastStateStarted,
        BroadcastStateStopped, BroadcastStatePaused
     ]:
    msg_type = data.get('type')
    try:
        msg_type = BroadcastMessageType(msg_type)
    except ValueError:
        raise BroadcastJsonError(
            'Broadcast message with unknown type: %i - %s' % (msg_type, data)
        )

    if msg_type == BroadcastMessageType.GameStreamState:
        state = data.get('state')
        try:
            state = GameStreamState(state)
            return STATE_MAP[state].parse_obj(data)
        except ValueError:
            raise BroadcastJsonError(
                'Broadcast message with unknown state: %i - %s' % (state, data)
            )

    return TYPE_MAP[msg_type].parse_obj(data)
