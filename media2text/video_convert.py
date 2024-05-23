"""Module for converting an image to text using a font."""

import time
import os
import subprocess
import threading
from enum import Enum

import cv2

from .image_query_font import ImageQueryFont
from .helpers import estimate_new_size, ready_render_temp
from .constants import RENDER_TEMP_DIR, PROCESS_REFRESH_RATE


# because cv2 is a C module...
# pylint: disable=maybe-no-member


class VideoChunkStatus(Enum):
    """Enum for the status of a video chunk."""

    PENDING = 0
    RUNNING = 1
    READY = 2


class VideoChunk:
    """Class representing a chunk of a video."""

    def __init__(
        self,
        video: str,
        start_time: int,
        length: int,
        frame_rate: int,
        new_size: tuple[int, int],
    ):
        self.name = os.path.join(RENDER_TEMP_DIR, f"temp_{start_time}.mp4")
        self.ffmpeg_command = (
            f"ffmpeg -ss {start_time} -i {video} -vf scale={new_size[0]}:{new_size[1]} "
            + f"-frames:v {frame_rate*length} -r {frame_rate} -c:v libx264 -an {self.name}"
        )
        self.status = VideoChunkStatus.PENDING

    def process(self):
        """Process the video chunk using FFmpeg.

        Raises:
            ValueError: If FFmpeg fails to process the video chunk.
        """
        if self.status == VideoChunkStatus.READY:
            return
        self.status = VideoChunkStatus.RUNNING
        try:
            subprocess.run(
                self.ffmpeg_command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            os.remove(self.name)
            print(e)
            return
        self.status = VideoChunkStatus.READY

    def __del__(self):
        if os.path.exists(self.name):
            os.remove(self.name)


class VideoChunkHandler:
    """Class for handling video chunks."""

    def __init__(
        self,
        video: str,
        frame_rate: int,
        new_size: tuple[int, int],
        chunk_length: int,
    ):
        ready_render_temp()
        self.video = video
        self.frame_rate = frame_rate
        self.new_size = new_size
        self.chunk_length = chunk_length
        video_capture = cv2.VideoCapture(video)
        self.video_length = video_capture.get(
            cv2.CAP_PROP_FRAME_COUNT
        ) / video_capture.get(cv2.CAP_PROP_FPS)
        video_capture.release()
        self.time = 0
        self.curr_chunk: VideoChunk = None
        self.next_chunk: VideoChunk = None
        self.stop = False
        threading.Thread(target=self._process_chunks, daemon=True).start()
        self.set_time(0)

    def __del__(self):
        self.stop = True

    def _process_chunks(self):
        while not self.stop:
            if self.next_chunk is not None:
                self.next_chunk.process()
            time.sleep(PROCESS_REFRESH_RATE)

    def _next_chunk(self):
        while self.next_chunk.status != VideoChunkStatus.READY:
            time.sleep(PROCESS_REFRESH_RATE)
        self.curr_chunk = self.next_chunk
        self.time += self.chunk_length
        self.next_chunk = VideoChunk(
            self.video,
            self.time,
            self.chunk_length,
            self.frame_rate,
            self.new_size,
        )

    def set_time(self, new_time: int):
        """Set the time of the video for next chunk.

        Args:
            new_time (int): New time in seconds.
        """
        self.time = new_time
        self.next_chunk = VideoChunk(
            self.video,
            self.time,
            self.chunk_length,
            self.frame_rate,
            self.new_size,
        )
        self._next_chunk()

    def iter_frames(self):
        """Iterate over the frames of the video."""
        while True:
            while self.curr_chunk.status != VideoChunkStatus.READY:
                time.sleep(PROCESS_REFRESH_RATE)
            video_capture = cv2.VideoCapture(self.curr_chunk.name)
            while True:
                success, frame = video_capture.read()
                if not success:
                    break
                yield frame
            video_capture.release()
            self._next_chunk()
            if self.time >= self.video_length:
                while True:
                    yield frame


class TextVideoPlayer:
    """Class for 'playing' a video as text."""

    def __init__(
        self,
        font: ImageQueryFont,
        video: str,
        frame_rate: int,
        num_characters_per_frame: int,
        row_spacing: float = 1.0,
        distance_metric: str = "manhattan",
        chunk_length: int = 5,
    ):
        self.font = font
        self.video = video
        self.frame_rate = frame_rate
        self.distance_metric = distance_metric
        self.chunk_length = chunk_length
        video_capture = cv2.VideoCapture(video)
        original_size = (
            int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
        video_capture.release()
        self.new_size = estimate_new_size(
            font, original_size, num_characters_per_frame, row_spacing
        )
        self.video_chunk_handler = VideoChunkHandler(
            video, frame_rate, self.new_size, chunk_length
        )

    def set_time(self, new_time: int):
        """Set the time of the video.

        Args:
            new_time (int): New time in seconds.
        """
        self.video_chunk_handler.set_time(new_time)

    def iter_frames(self):
        """Iterate over the frames of the video and convert them to text."""
        for frame in self.video_chunk_handler.iter_frames():
            yield self.font.query(frame, self.distance_metric)
