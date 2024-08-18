"""Module for converting an image to text using a font."""

import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
from enum import Enum

import cv2

from .constants import (BYTE_ORDER, INT_SIZE, PROCESS_REFRESH_RATE,
                        RENDER_TEMP_DIR, TEXT_VIDEO_MAGIC_NUMBER)
from .helpers import estimate_new_size
from .image_query_font import ImageQueryFont

# because cv2 is a C module...
# pylint: disable=maybe-no-member


class VideoChunkStatus(Enum):
    """Enum for the status of a video chunk."""

    PENDING = 0
    RUNNING = 1
    READY = 2
    DELETED = 3


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
        chunk_file = tempfile.NamedTemporaryFile(
            dir=RENDER_TEMP_DIR, prefix=f"s{start_time}_", suffix=".mkv", delete=False
        )
        self.name = chunk_file.name
        self.ffmpeg_command = [
            "ffmpeg",
            "-ss",
            str(start_time),
            "-i",
            video,
            "-y",
            "-vf",
            f"fps={frame_rate}, scale={new_size[0]}:{new_size[1]}:flags=lanczos",
            "-frames:v",
            str(frame_rate * length),
            "-c:v",
            "libx264",
            "-crf",
            "0",
            "-an",
            self.name,
        ]
        self.status = VideoChunkStatus.PENDING
        self.capture = None

    def process(self):
        """Process the video chunk using FFmpeg."""
        if self.status in (VideoChunkStatus.READY, VideoChunkStatus.DELETED):
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
            print(e, file=sys.stderr)
        self.status = VideoChunkStatus.READY
        self.capture = cv2.VideoCapture(self.name)

    def delete(self):
        """Delete the video chunk file."""
        if self.status == VideoChunkStatus.DELETED:
            return
        self.status = VideoChunkStatus.DELETED
        if self.capture is not None:
            self.capture.release()
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
        self._stopped = False
        threading.Thread(target=self._process_chunks, daemon=True).start()
        self.set_time(0)

    def _process_chunks(self):
        while not self._stopped:
            if self.next_chunk is not None:
                self.next_chunk.process()
            time.sleep(PROCESS_REFRESH_RATE)

    def _next_chunk(self):
        while self.next_chunk.status != VideoChunkStatus.READY:
            time.sleep(PROCESS_REFRESH_RATE)
        if self.curr_chunk is not None:
            self.curr_chunk.delete()
        self.curr_chunk = self.next_chunk
        self.next_chunk_time += self.chunk_length
        if self.next_chunk_time >= self.video_length:
            return
        self.next_chunk = VideoChunk(
            self.video,
            self.next_chunk_time,
            self.chunk_length,
            self.frame_rate,
            self.new_size,
        )

    def stop(self):
        """Stop the video chunk handler (cannot be resumed)."""
        if self._stopped:
            return
        if self.curr_chunk is not None:
            self.curr_chunk.delete()
        if self.next_chunk is not None:
            self.next_chunk.delete()
        self._stopped = True

    def set_time(self, new_time: int):
        """Set the time of the video for next chunk.

        Args:
            new_time (int): New time in seconds.
        """
        if self._stopped:
            raise ValueError("Video chunk handler has been stopped")
        self.next_chunk_time = new_time
        if self.next_chunk is not None:
            self.next_chunk.delete()
        if self.next_chunk_time >= self.video_length:
            return
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
            while self.curr_chunk.status not in (
                VideoChunkStatus.READY,
                VideoChunkStatus.DELETED,
            ):
                time.sleep(PROCESS_REFRESH_RATE)
            if self._stopped:
                raise ValueError("Video chunk handler has been stopped")
            video_capture = self.curr_chunk.capture
            if video_capture is None:
                raise ValueError("Chunk capture should not be None")
            while True:
                success, frame = video_capture.read()
                if not success:
                    break
                yield frame
            if self.next_chunk_time >= self.video_length:
                break
            self._next_chunk()


class TextVideo:
    """Class for converting video to text."""

    def __init__(
        self,
        font: ImageQueryFont,
        video: str,
        frame_rate: int = 30,
        num_characters_per_frame: int = 5000,
        row_spacing: float = 1.0,
        distance_metric: str = "manhattan",
        chunk_length: int = 5,
        buffer_size: int = 100,
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
        self.buffer_size = buffer_size
        video_capture = cv2.VideoCapture(video)
        original_size = (
            int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
        video_capture.release()
        self.new_size = estimate_new_size(
            font, original_size, num_characters_per_frame, row_spacing
        )
        self._video_chunk_handler = VideoChunkHandler(
            video, frame_rate, self.new_size, chunk_length
        )
        self._frame_generator = (
            self._iter_frames_from_video()
            if not self.from_render
            else self._iter_frames_from_render()
        )
        self._stopped = False

    def _set_time_from_video(self, new_time: int):
        self._video_chunk_handler.set_time(new_time)

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
        if self._stopped:
            raise ValueError("Video player has been stopped")
        if new_time < 0 or new_time >= self._video_chunk_handler.video_length:
            return
        if not self.from_render:
            self._set_time_from_video(new_time)
        else:
            self._set_time_from_render(new_time)
        self._frame_generator = (
            self._iter_frames_from_video()
            if not self.from_render
            else self._iter_frames_from_render()
        )

    def _iter_frames_from_video(self):
        q = queue.Queue(self.buffer_size)
        video_frame_generator = self._video_chunk_handler.iter_frames()

        def buffer_frames():
            while True:
                if q.qsize() < self.buffer_size:
                    try:
                        frame = next(video_frame_generator)
                    except StopIteration:
                        break
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

    def change_font(self, font: ImageQueryFont):
        """Change the font of the video.

        Args:
            font (ImageQueryFont): New font to use.
        """
        self.font = font

    def next_frame(self):
        """Get the next frame of the video.

        Returns:
            str: Next frame of the video.
        """
        if self._stopped:
            raise ValueError("Video player has been stopped")
        return next(self._frame_generator)

    def stop(self):
        """Stop the video player (cannot be resumed)."""
        if self._stopped:
            return
        if self.from_render:
            self.file_pointer.close()
        self._video_chunk_handler.stop()
        self._stopped = True

    def save(self, path: str):
        """Function to save a video to a file.

        Args:
            video_player (TextVideoPlayer): Video player to save.
            path (str): Path to save the video.
        """
        if self._stopped:
            raise ValueError("Video player has been stopped")
        self.set_time(0)
        frame_count = 0
        with open(path + ".tmp", "wb") as file:
            for frame in self._frame_generator:
                frame_bytes = frame.encode("utf-8")
                file.write(len(frame_bytes).to_bytes(INT_SIZE, BYTE_ORDER))
                file.write(frame_bytes)
                frame_count += 1
        with open(path, "wb") as file:
            file.write(TEXT_VIDEO_MAGIC_NUMBER.to_bytes(INT_SIZE, BYTE_ORDER))
            file.write(self.frame_rate.to_bytes(INT_SIZE, BYTE_ORDER))
            file.write(frame_count.to_bytes(INT_SIZE, BYTE_ORDER))
            frames_offset = 3 * INT_SIZE + frame_count * INT_SIZE
            with open(path + ".tmp", "rb") as tmp_file:
                for _ in range(frame_count):
                    offset = tmp_file.tell() + frames_offset
                    file.write(offset.to_bytes(INT_SIZE, BYTE_ORDER))
                    frame_size = int.from_bytes(tmp_file.read(INT_SIZE), BYTE_ORDER)
                    tmp_file.seek(frame_size, 1)
                tmp_file.seek(0)
                for _ in range(frame_count):
                    frame_size = int.from_bytes(tmp_file.read(INT_SIZE), BYTE_ORDER)
                    frame = tmp_file.read(frame_size)
                    file.write(frame_size.to_bytes(INT_SIZE, BYTE_ORDER))
                    file.write(frame)
                file.write(tmp_file.read())
            os.remove(path + ".tmp")
