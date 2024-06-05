"""Module for converting an image to text using a font."""

import time
import os
import subprocess
import threading
import queue
from enum import Enum

import cv2

from .image_query_font import ImageQueryFont
from .helpers import estimate_new_size, ready_render_temp
from .constants import (
    RENDER_TEMP_DIR,
    PROCESS_REFRESH_RATE,
    TEXT_VIDEO_MAGIC_NUMBER,
    BYTE_ORDER,
    INT_SIZE,
)


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
        self.name = os.path.join(RENDER_TEMP_DIR, f"temp_{start_time}.mkv")
        self.ffmpeg_command = (
            f'ffmpeg -ss {start_time} -i "{video}" -vf "fps={frame_rate}, '
            + f'scale={new_size[0]}:{new_size[1]}:flags=lanczos" '
            + f"-frames:v {frame_rate*length} -c:v libx264 -crf 0 -an {self.name}"
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
            if os.path.exists(self.name):
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
        self.next_chunk_time = 0
        self.curr_chunk: VideoChunk = None
        self.next_chunk: VideoChunk = None
        video_capture = cv2.VideoCapture(video)
        self.video_length = int(
            video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
            / video_capture.get(cv2.CAP_PROP_FPS)
        )
        self.stop = False
        threading.Thread(target=self._process_chunks, daemon=True).start()
        self.set_time(0)

    def __del__(self):
        self.stop = True
        ready_render_temp()

    def _process_chunks(self):
        while not self.stop:
            if self.next_chunk is not None:
                self.next_chunk.process()
            time.sleep(PROCESS_REFRESH_RATE)

    def _next_chunk(self):
        while self.next_chunk.status != VideoChunkStatus.READY:
            time.sleep(PROCESS_REFRESH_RATE)
        self.curr_chunk = self.next_chunk
        self.next_chunk_time += self.chunk_length
        self.next_chunk = VideoChunk(
            self.video,
            self.next_chunk_time,
            self.chunk_length,
            self.frame_rate,
            self.new_size,
        )

    def set_time(self, new_time: int):
        """Set the time of the video for next chunk.

        Args:
            new_time (int): New time in seconds.
        """
        self.next_chunk_time = new_time
        self.next_chunk = VideoChunk(
            self.video,
            self.next_chunk_time,
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
            if self.next_chunk_time >= self.video_length:
                break


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
        self.from_render = False
        with open(video, "rb") as file:
            magic_number = int.from_bytes(file.read(INT_SIZE), BYTE_ORDER)
            if magic_number == TEXT_VIDEO_MAGIC_NUMBER:
                self.from_render = True
                self.frame_rate = int.from_bytes(file.read(INT_SIZE), BYTE_ORDER)
                self.frame_count = int.from_bytes(file.read(INT_SIZE), BYTE_ORDER)
                self.frames_offset = 3 * INT_SIZE + self.frame_count * INT_SIZE
        if self.from_render:
            self.file_pointer = open(video, "rb")
            return
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

    def _set_time_from_video(self, new_time: int):
        self.video_chunk_handler.set_time(new_time)

    def _set_time_from_render(self, new_time: int):
        frame_number = new_time * self.frame_rate
        self.file_pointer.seek(3 * INT_SIZE + frame_number * INT_SIZE)
        frame_offset = int.from_bytes(self.file_pointer.read(INT_SIZE), BYTE_ORDER)
        self.file_pointer.seek(frame_offset)

    def set_time(self, new_time: int):
        """Set the time of the video.

        Args:
            new_time (int): New time in seconds.
        """
        if new_time < 0 or new_time >= self.video_chunk_handler.video_length:
            return
        if not self.from_render:
            self._set_time_from_video(new_time)
        else:
            self._set_time_from_render(new_time)

    def _iter_frames_from_video(self, buffer_size: int):
        q = queue.Queue(buffer_size)
        video_frame_generator = self.video_chunk_handler.iter_frames()

        def buffer_frames():
            while True:
                if q.qsize() < buffer_size:
                    frame = next(video_frame_generator)
                    q.put(self.font.query(frame, self.distance_metric))
                else:
                    time.sleep(PROCESS_REFRESH_RATE)

        threading.Thread(target=buffer_frames, daemon=True).start()
        while True:
            try:
                frame = q.get(block=True, timeout=5)
                yield frame
            except queue.Empty:
                break

    def _iter_frames_from_render(self):
        while True:
            frame_size_bytes = self.file_pointer.read(INT_SIZE)
            if not frame_size_bytes:
                break
            frame_size = int.from_bytes(frame_size_bytes, BYTE_ORDER)
            frame_bytes = self.file_pointer.read(frame_size)
            yield frame_bytes.decode("utf-8")

    def iter_frames(self, buffer_size: int = 100):
        """Iterate over the frames of the video and convert them to text."""
        generator = (
            self._iter_frames_from_video(buffer_size)
            if not self.from_render
            else self._iter_frames_from_render()
        )
        for item in generator:
            yield item
