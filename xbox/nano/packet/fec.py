# flake8: noqa
from construct import *
from xbox.sg.utils.struct import XStruct

# Microsoft::Rdp::Dct::MuxDCTChannelFECLayer::AddOutgoingPacket
fec_packet = XStruct(
    'unk1' / Int8ul,
    'unk2' / Int16ul
)


# Microsoft::Rdp::Dct::MuxDCTChannelFECLayerVariableBlockLength::FECCommonHeader::Serialize
fec_common_header = XStruct(
    'unk1' / Int8ul,
    # if v2 & 2
    'unk2' / Int8ul,
    'unk3' / Int32ul,
    'unk4' / Int16ul
)

# Microsoft::Rdp::Dct::MuxDCTChannelFECLayerVariableBlockLength::FECLayerStatistics::Deserialize
fec_layer_statistics = XStruct(
    'unk1' / Int8ul,
    'unk2' / Int64ul,
    'unk3' / Float32l,
    'unk4' / Int16ul,
    'unk5' / Int16ul,
    'unk6' / Int16ul,
    'unk7' / Int16ul,
    'unk8' / Int16ul,
    'unk9' / Float32l
)

