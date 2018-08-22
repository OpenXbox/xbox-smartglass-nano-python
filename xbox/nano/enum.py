from enum import Enum


class ChannelClass(Enum):
    Video = 'Microsoft::Rdp::Dct::Channel::Class::Video'
    Audio = 'Microsoft::Rdp::Dct::Channel::Class::Audio'
    ChatAudio = 'Microsoft::Rdp::Dct::Channel::Class::ChatAudio'
    Control = 'Microsoft::Rdp::Dct::Channel::Class::Control'
    Input = 'Microsoft::Rdp::Dct::Channel::Class::Input'
    InputFeedback = 'Microsoft::Rdp::Dct::Channel::Class::Input Feedback'
    TcpBase = 'Microsoft::Rdp::Dct::Channel::Class::TcpBase'


class RtpPayloadType(Enum):
    Streamer = 0x23
    Control = 0x60
    ChannelControl = 0x61
    UDPHandshake = 0x64


class ChannelControlPayloadType(Enum):
    ClientHandshake = 0x0  # SYN
    ServerHandshake = 0x1  # ACK
    # Channel requests
    ChannelCreate = 0x2
    ChannelOpen = 0x3
    ChannelClose = 0x4


class AudioPayloadType(Enum):
    ServerHandshake = 0x1
    ClientHandshake = 0x2
    Control = 0x3
    Data = 0x4


class VideoPayloadType(Enum):
    ServerHandshake = 0x1
    ClientHandshake = 0x2
    Control = 0x3
    Data = 0x4


class InputPayloadType(Enum):
    ServerHandshake = 0x1
    ClientHandshake = 0x2
    FrameAck = 0x3
    Frame = 0x4


class ControlPayloadType(Enum):
    Unknown = 0x0
    SessionInit = 0x1  # Unused
    SessionCreate = 0x2
    SessionCreateResponse = 0x3
    SessionDestroy = 0x4
    VideoStatistics = 0x5
    RealtimeTelemetry = 0x6
    ChangeVideoQuality = 0x7
    InitiateNetworkTest = 0x8
    NetworkInformation = 0x9
    NetworkTestResponse = 0xA
    ControllerEvent = 0xB


class ControllerEvent(Enum):
    Removed = 0x0
    Added = 0x1


class AudioCodec(Enum):
    Opus = 0x0
    AAC = 0x1
    PCM = 0x2


class AudioBitDepthType(Enum):
    Integer = 0x0
    Float = 0x1


class VideoCodec(Enum):
    H264 = 0x0
    YUV = 0x1  # Actually can be IYUV or NV12 based on another field
    RGB = 0x2


class BroadcastMessageType(Enum):
    Unknown = 0x0
    StartGameStream = 0x1
    StopGameStream = 0x2
    GameStreamState = 0x3
    GameStreamEnabled = 0x4
    GameStreamError = 0x5
    Telemetry = 0x6
    PreviewStatus = 0x7


class VideoQuality(object):
    VeryHigh = [12000000, 3, 60000, 1001, 59, 0]
    High = [8000000, 2, 60000, 1001, 59, 0]
    Middle = [6000002, 2, 60000, 1001, 3600, 0]
    Low = [3000001, 1, 30000, 1001, 3600, 0]


class GameStreamError(Enum):
    Unknown = 0x0
    General = 0x1
    FailedToInstantiate = 0x2
    FailedToInitialize = 0x3
    FailedToStart = 0x4
    FailedToStop = 0x5
    NoController = 0x6
    DifferentMsaActive = 0x7
    DrmVideo = 0x8
    HdcpVideo = 0x9
    KinectTitle = 0xA
    ProhibitedGame = 0xB
    PoorNetworkConnection = 0xC
    StreamingDisabled = 0xD
    CannotReachConsole = 0xE
    GenericError = 0xF
    VersionMismatch = 0x10
    NoProfile = 0x11
    BroadcastInProgress = 0x12


class GameStreamState(Enum):
    Unknown = 0x0
    Initializing = 0x1
    Started = 0x2
    Stopped = 0x3
    Paused = 0x4


# class StreamerChannel(Enum):
#     Control = 0x0
#     Video = 0x1
#     Audio = 0x2
#     Input = 0x3
