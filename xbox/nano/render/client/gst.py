import logging
import asyncio
from typing import Optional
from asyncio import Queue

import gi
from gi.repository import Gst, GObject, GLib

from xbox.nano.render.client.base import Client
from xbox.nano.render.audio.aac import AACFrame, AACProfile

gi.require_version('Gst', '1.0')
log = logging.getLogger(__name__)


class GstClient(Client):
    def __init__(self):
        self.protocol = None

        self._running = False
        self._loop_task: Optional[asyncio.Task] = None

        self._video_frames = Queue()
        self._audio_frames = Queue()

        GObject.threads_init()
        Gst.init(None)

        self.pipeline = Gst.Pipeline.new("nanostream")

        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message)

        # stream-type=stream should set appsrc to PUSH mode
        video_pipeline = " ! ".join([
            "appsrc name=videosrc stream-type=stream",
            "decodebin",
            "videoconvert",
            "queue",
            "autovideosink"
        ])

        audio_pipeline = " ! ".join([
            "appsrc name=audiosrc stream-type=stream",
            "decodebin",
            "audioconvert",
            "queue",
            "autoaudiosink"
        ])

        pipeline_string = video_pipeline + " " + audio_pipeline
        log.debug("Gst Pipeline: %s" % pipeline_string)
        self.pipeline = Gst.parse_launch(pipeline_string)

        self.a_src = self.pipeline.get_by_name("audiosrc")
        self.v_src = self.pipeline.get_by_name("videosrc")

        self.a_src.connect('need-data', self.need_data)
        self.v_src.connect('need-data', self.need_data)
        self.a_src.connect('enough-data', self.enough_data)
        self.v_src.connect('enough-data', self.enough_data)

        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            raise Exception("Unable to set the pipeline to the playing state")

        self.context = GLib.MainContext.default()

        super(GstClient, self).__init__(None, None, None)

    def open(self, protocol):
        log.debug('Opening client')
        self.protocol = protocol
        self.start_loop()

    def close(self):
        self._running = False

    def start_loop(self):
        self._loop_task = asyncio.create_task(self.loop())

    async def loop(self):
        self._running = True
        while self._running:
            self.pump()
            await asyncio.sleep(0.0)

    def pump(self):
        self.context.iteration(may_block=False)

    def on_message(self, bus, message):
        struct = message.get_structure()

        if message.type == Gst.MessageType.EOS:
            log.debug('EOS')

        elif message.type == Gst.MessageType.TAG and message.parse_tag() and struct.has_field('taglist'):
            log.debug('TAG')
            taglist = struct.get_value('taglist')
            for x in range(taglist.n_tags()):
                name = taglist.nth_tag_name(x)
                log.debug('  %s: %s' % (name, taglist.get_string(name)[1]))

        elif message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            log.error("Error: %s" % err, debug)

        elif message.type == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            log.warning("Warning: %s" % err, debug)

        elif message.type == Gst.MessageType.STATE_CHANGED:
            old_state, new_state, pending_state = message.parse_state_changed()
            if message.src == self.pipeline:
                log.debug("Pipeline state changed from '{0:s}' to '{1:s}'".format(
                    Gst.Element.state_get_name(old_state),
                    Gst.Element.state_get_name(new_state)))

        else:
            log.error('Unhandled messagetype: %s' % message.type)

    def need_data(self, src, length):
        if src == self.v_src:
            frame_buf = self._video_frames
        elif src == self.a_src:
            frame_buf = self._audio_frames
        else:
            raise Exception('src %s is not handled' % src.get_name())

        # log.debug('%s needs %i bytes of data' % (src.get_name(), length))
        try:
            data = frame_buf.get_nowait()
        except asyncio.QueueEmpty as e:
            # log.debug('%s Queue is empty %s' % (src.get_name(), e))
            # FIXME: Passing an empty buffer produces:
            # FIXME: GStreamer-CRITICAL **: gst_memory_get_sizes: assertion 'mem != NULL' failed
            data = b''

        buf = Gst.Buffer.new_wrapped(data)
        src.emit("push-buffer", buf)

    def enough_data(self, src):
        log.debug('Enough data for %s' % src.get_name())

    def set_video_format(self, video_fmt):
        pass

    def set_audio_format(self, audio_fmt):
        pass

    def render_video(self, data):
        self._video_frames.put(data)

    def render_audio(self, data):
        data = AACFrame.generate_header(len(data), AACProfile.Main, 48000, 2) + data
        self._audio_frames.put(data)

    def send_input(self, frame, timestamp):
        pass

    def controller_added(self, controller_index):
        pass

    def controller_removed(self, controller_index):
        pass
