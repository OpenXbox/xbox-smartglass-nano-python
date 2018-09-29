from xbox.nano.render.client.base import Client
from xbox.nano.render.audio.aac import AACFrame, AACProfile


class FileClient(Client):
    def __init__(self, filename, save_frames=False):
        self.filename = filename
        self.save_frames = save_frames

        self._audio_fmt = None
        self._video_file = None
        self._audio_file = None
        self._video_frame_index = 0
        self._audio_frame_index = 0
        super(FileClient, self).__init__(None, None, None)

    def open(self, protocol):
        if not self.save_frames:
            self._video_file = open('%s.video.raw' % self.filename, 'wb')
            self._audio_file = open('%s.audio.raw' % self.filename, 'wb')

    def close(self):
        if not self.save_frames:
            self._video_file.close()
            self._audio_file.close()

    def loop(self):
        pass

    def pump(self):
        pass

    def set_video_format(self, video_fmt):
        pass

    def set_audio_format(self, audio_fmt):
        self._audio_fmt = audio_fmt

    def render_video(self, data):
        # Video frames can be written as-is
        if not self.save_frames:
            self._video_file.write(data)
        else:
            with open('%s.video.%08d.frame' % (self.filename, self._video_frame_index), 'wb') as f:
                f.write(data)
            self._video_frame_index += 1

    def render_audio(self, data):
        if not self._audio_fmt:
            raise Exception(
                "No audio format set, cannot create frame header"
            )
        # Audio frames need a header prepended
        data = AACFrame.generate_header(
            len(data), AACProfile.Main,
            self._audio_fmt.sample_rate,
            self._audio_fmt.channels
        ) + data

        if not self.save_frames:
            self._audio_file.write(data)
        else:
            with open('%s.audio.%08d.frame' % (self.filename, self._audio_frame_index), 'wb') as f:
                f.write(data)
            self._audio_frame_index += 1

    def send_input(self, frame, timestamp):
        pass

    def controller_added(self, controller_index):
        pass

    def controller_removed(self, controller_index):
        pass
