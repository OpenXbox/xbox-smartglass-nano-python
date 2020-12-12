import pytest
from xbox.nano.packet import json
from xbox.nano.enum import BroadcastMessageType, GameStreamState


def test_invalid_msg_type():
    with pytest.raises(json.BroadcastJsonError):
        json.parse(dict(type=42))


def test_invalid_state():
    with pytest.raises(json.BroadcastJsonError):
        json.parse(
            dict(type=42, state=99)
        )


def test_stream_enabled(json_messages):
    data = json_messages['broadcast_stream_enabled']
    msg = json.parse(data)

    assert msg.type == BroadcastMessageType.GameStreamEnabled.value
    assert msg.enabled is True
    assert msg.canBeEnabled is True
    assert msg.majorProtocolVersion == 6
    assert msg.minorProtocolVersion == 0


def test_start_stream(json_messages):
    _config = {
        "urcpType": "0",
        "urcpFixedRate": "-1",
        "urcpMaximumWindow": "1310720",
        "urcpMinimumRate": "256000",
        "urcpMaximumRate": "10000000",
        "urcpKeepAliveTimeoutMs": "0",
        "audioFecType": "0",
        "videoFecType": "0",
        "videoFecLevel": "3",
        "videoPacketUtilization": "0",
        "enableDynamicBitrate": "false",
        "dynamicBitrateScaleFactor": "1",
        "dynamicBitrateUpdateMs": "5000",
        "sendKeyframesOverTCP": "false",
        "videoMaximumWidth": "1280",
        "videoMaximumHeight": "720",
        "videoMaximumFrameRate": "60",
        "videoPacketDefragTimeoutMs": "16",
        "enableVideoFrameAcks": "false",
        "enableAudioChat": "true",
        "audioBufferLengthHns": "10000000",
        "audioSyncPolicy": "1",
        "audioSyncMinLatency": "10",
        "audioSyncDesiredLatency": "40",
        "audioSyncMaxLatency": "170",
        "audioSyncCompressLatency": "100",
        "audioSyncCompressFactor": "0.99",
        "audioSyncLengthenFactor": "1.01",
        "enableOpusAudio": "false",
        "enableOpusChatAudio": "true",
        "inputReadsPerSecond": "120",
        "udpMaxSendPacketsInWinsock": "250",
        "udpSubBurstGroups": "5",
        "udpBurstDurationMs": "11"
    }

    data = json_messages['broadcast_start_stream']
    msg = json.parse(data)

    assert msg.type == BroadcastMessageType.StartGameStream.value
    assert msg.reQueryPreviewStatus is True
    assert msg.configuration == _config


@pytest.mark.skip()
def test_stop_stream(json_messages):
    data = json_messages['broadcast_stop_stream']
    msg = json.parse(data)

    assert msg.type == BroadcastMessageType.StopGameStream.value


def test_state_unknown(json_messages):
    data = json_messages['broadcast_state_unknown']
    msg = json.parse(data)

    assert msg.type == BroadcastMessageType.GameStreamState.value
    assert msg.state == GameStreamState.Unknown.value
    assert msg.sessionId == ''


def test_state_init(json_messages):
    data = json_messages['broadcast_state_init']
    msg = json.parse(data)

    assert msg.type == BroadcastMessageType.GameStreamState.value
    assert msg.state == GameStreamState.Initializing.value
    assert msg.sessionId == '{14608F3C-1C4A-4F32-9DA6-179CE1001E4A}'
    assert msg.udpPort == 49665
    assert msg.tcpPort == 53394


def test_state_started(json_messages):
    data = json_messages['broadcast_state_started']
    msg = json.parse(data)

    assert msg.type == BroadcastMessageType.GameStreamState.value
    assert msg.state == GameStreamState.Started.value
    assert msg.sessionId == '{14608F3C-1C4A-4F32-9DA6-179CE1001E4A}'
    assert msg.isWirelessConnection is False
    assert msg.wirelessChannel == 0
    assert msg.transmitLinkSpeed == 1000000000


def test_state_stopped(json_messages):
    data = json_messages['broadcast_state_stopped']
    msg = json.parse(data)

    assert msg.type == BroadcastMessageType.GameStreamState.value
    assert msg.state == GameStreamState.Stopped.value
    assert msg.sessionId == '{14608F3C-1C4A-4F32-9DA6-179CE1001E4A}'


@pytest.mark.skip()
def test_error(json_messages):
    data = json_messages['broadcast_error']
    msg = json.parse(data)

    assert msg.type == BroadcastMessageType.GameStreamError.value


@pytest.mark.skip()
def test_telemetry(json_messages):
    data = json_messages['broadcast_telemetry']
    msg = json.parse(data)

    assert msg.type == BroadcastMessageType.Telemetry.value


def test_previewstatus(json_messages):
    data = json_messages['broadcast_previewstatus']
    msg = json.parse(data)

    assert msg.type == BroadcastMessageType.PreviewStatus.value
    assert msg.isPublicPreview is False
    assert msg.isInternalPreview is False
