from av import audio


class AACProfile(object):
    Main = 0
    Lc = 1
    Ssr = 2
    Ltp = 3


class AACFrame(object):
    """
    Use like this, on each audio frame:
        frame_size = len(msg.payload.payload.data)
        frame = AACFrame.gen_adts_header(frame_size, AACProfile.Main, 48000, 2)
        frame += msg.payload.payload.data
        ... deliver to audio sink
    """
    sampling_freq_index = {
        96000: 0,
        88200: 1,
        64000: 2,
        48000: 3,
        44100: 4,
        32000: 5,
        24000: 6,
        22050: 7,
        16000: 8,
        12000: 9,
        11025: 10,
        8000: 11,
        7350: 12
    }
    ADTS_HEADER_LEN = 7

    @staticmethod
    def generate_header(frame_size, aac_profile, sampling_freq, channels):
        header_id = 0  # MPEG4
        adts_headers = bytearray(AACFrame.ADTS_HEADER_LEN)
        frame_size += AACFrame.ADTS_HEADER_LEN
        sampling_index = AACFrame.sampling_freq_index[sampling_freq]

        adts_headers[0] = 0xFF
        adts_headers[1] = 0xF0 | (header_id << 3) | 0x1
        adts_headers[2] = (aac_profile << 6) | (sampling_index << 2) | 0x2 | \
                          (channels & 0x4)
        adts_headers[3] = ((channels & 0x3) << 6) | 0x30 | (frame_size >> 11)
        adts_headers[4] = ((frame_size >> 3) & 0x00FF)
        adts_headers[5] = (((frame_size & 0x0007) << 5) + 0x1F)
        adts_headers[6] = 0xFC

        return adts_headers


class AACResampler(object):
    """
    Resampler should be used to convert AAC data from planar->packet format
    """
    def __init__(self, sample_format, samplerate, channels):
        layout = audio.layout.AudioLayout(channels)
        self.resampler = audio.resampler.AudioResampler(format=sample_format,
                                                        layout=layout,
                                                        rate=samplerate)

    def resample(self, frame):
        return self.resampler.resample(frame)
