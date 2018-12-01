import av
from xbox.nano.enum import VideoCodec, AudioCodec


class FrameDecoder(object):
    def __init__(self, codec_name):
        self._decoder = av.Codec(codec_name, 'r').create()

    @classmethod
    def video(cls, codec_id):
        if VideoCodec.H264 == codec_id:
            return cls('h264')
        elif VideoCodec.YUV == codec_id:
            return cls('yuv420p')
        elif VideoCodec.RGB == codec_id:
            return cls('rgb')
        else:
            raise Exception('FrameDecoder was supplied invalid VideoCodec')

    @classmethod
    def audio(cls, codec_id):
        if AudioCodec.AAC == codec_id:
            return cls('aac')
        elif AudioCodec.Opus == codec_id:
            return cls('opus')
        elif AudioCodec.PCM == codec_id:
            return cls('pcm')
        else:
            raise Exception('FrameDecoder was supplied invalid AudioCodec')

    def decode(self, data):
        packet = av.packet.Packet(data)
        return self._decoder.decode(packet)
