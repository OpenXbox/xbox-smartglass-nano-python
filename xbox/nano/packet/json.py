from marshmallow_objects import Model, fields
from marshmallow_enum import EnumField
from xbox.nano.enum import BroadcastMessageType, GameStreamState


class BroadcastJsonError(Exception):
    pass


class _BroadcastMessage(Model):
    type = EnumField(BroadcastMessageType, by_value=True)


class BroadcastStreamEnabled(_BroadcastMessage):
    enabled = fields.Bool()
    canBeEnabled = fields.Bool()
    majorProtocolVersion = fields.Int()
    minorProtocolVersion = fields.Int()


class BroadcastPreviewStatus(_BroadcastMessage):
    isPublicPreview = fields.Bool()
    isInternalPreview = fields.Bool()


class BroadcastStartStream(_BroadcastMessage):
    configuration = fields.Dict()
    reQueryPreviewStatus = fields.Bool(default=False)


class BroadcastStopStream(_BroadcastMessage):
    pass


class BroadcastError(_BroadcastMessage):
    pass


class BroadcastTelemetry(_BroadcastMessage):
    pass


class _BroadcastStateMessage(_BroadcastMessage):
    state = EnumField(GameStreamState, by_value=True)
    sessionId = fields.Str()


class BroadcastStateUnknown(_BroadcastStateMessage):
    pass


class BroadcastStateInitializing(_BroadcastStateMessage):
    udpPort = fields.Int()
    tcpPort = fields.Int()


class BroadcastStateStarted(_BroadcastStateMessage):
    isWirelessConnection = fields.Bool()
    wirelessChannel = fields.Int()
    transmitLinkSpeed = fields.Int()


class BroadcastStateStopped(_BroadcastStateMessage):
    pass


class BroadcastStatePaused(_BroadcastStateMessage):
    pass


TYPE_MAP = {
    BroadcastMessageType.StartGameStream: BroadcastStartStream,
    BroadcastMessageType.StopGameStream: BroadcastStopStream,
    BroadcastMessageType.GameStreamState: _BroadcastStateMessage,
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


def parse(data):
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
            return STATE_MAP[state].load(data)
        except ValueError:
            raise BroadcastJsonError(
                'Broadcast message with unknown state: %i - %s' % (state, data)
            )

    return TYPE_MAP[msg_type].load(data)
