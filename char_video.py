"""Module containing the CharVideo class."""
import subprocess
import os
import time

import moviepy.editor as mpy
import numpy as np
import pygame.sndarray

from font import Font
from char_image import CharImage
from consts import (
    UNICODE_CHAR_BYTES,
    INT_BYTES,
    AUDIO_BYTES_PER_SAMPLE,
    RENDER_TEMPS_PATH,
)


class CharVideo:
    """Class representing a video made out of characters."""

    def __init__(
        self,
        source_path: str,
    ):
        # NOTE: CharVideo doesn't allow for creating of a CharVideo directly from a video file
        # because playing a CharVideo directly from a video file can be very slow
        # with some video formats and/or resolutions.
        # This can be fixed by pre-scaling the video to necessary size,
        # but that itself can take a long time, so it's better to just render the video to a file.

        # loading main data from the source file
        self.data_stream = open(source_path, "rb")
        font_bytes_len = int.from_bytes(self.data_stream.read(INT_BYTES))
        self.font = Font.from_bytes(self.data_stream.read(font_bytes_len))
        self.video_frame_rate = int.from_bytes(self.data_stream.read(INT_BYTES))
        video_frame_width = int.from_bytes(self.data_stream.read(INT_BYTES))
        video_frame_height = int.from_bytes(self.data_stream.read(INT_BYTES))
        self.video_frame_count = int.from_bytes(self.data_stream.read(INT_BYTES))
        self.audio_frame_rate = int.from_bytes(self.data_stream.read(INT_BYTES))
        self.audio_channel_count = int.from_bytes(self.data_stream.read(INT_BYTES))
        self.audio_segment_count = int.from_bytes(self.data_stream.read(INT_BYTES))
        # calculating offsets and sizes
        self.audio_segment_size = (
            self.audio_frame_rate * self.audio_channel_count * AUDIO_BYTES_PER_SAMPLE
        )
        self.audio_offset = self.data_stream.tell()
        self.video_frame_shape = (video_frame_width, video_frame_height)
        self.video_frame_size = (
            self.video_frame_shape[0] * self.video_frame_shape[1] * UNICODE_CHAR_BYTES
        )
        self.video_offset = (
            self.audio_offset + self.audio_segment_count * self.audio_segment_size
        )
        self.duration = self.video_frame_count // self.video_frame_rate

    def __del__(self):
        # making sure the data stream is closed on garbage collection
        self.data_stream.close()

    @staticmethod
    def _clear_render_temps():
        """Clears the render temps folder or creates it if it doesn't exist."""
        if not os.path.exists(RENDER_TEMPS_PATH):
            os.mkdir(RENDER_TEMPS_PATH)
            return
        for file in os.listdir(RENDER_TEMPS_PATH):
            os.remove(os.path.join(RENDER_TEMPS_PATH, file))

    @staticmethod
    def render(
        source_path: str,
        dest_path: str,
        char_count_per_frame: int | str,
        frame_rate: int | str,
        render_audio: bool,
        font: Font,
    ) -> "CharVideo":
        """
        Function for rendering a CharVideo from a video file.
        Yields progress messages.
        """
        if isinstance(char_count_per_frame, str):
            try:
                char_count_per_frame = int(char_count_per_frame)
            except ValueError as e:
                raise ValueError("Character count must be an integer") from e
        if char_count_per_frame < 1:
            raise ValueError("Character count must be greater than or equal to 1")
        if isinstance(frame_rate, str):
            try:
                frame_rate = int(frame_rate)
            except ValueError as e:
                raise ValueError("frame_rate must be an integer") from e
        if frame_rate < 1:
            raise ValueError("frame_rate must be greater that or equal to 1")
        if font is None:
            raise ValueError("Font must be set")
        # renders a char video from the given source_path with the given parameters
        # and saves it to dest_path
        t = time.time()
        CharVideo._clear_render_temps()
        video = mpy.VideoFileClip(source_path)
        size = CharImage.calculate_new_size(video.size, char_count_per_frame, font)
        video.close()
        # rendering a temporary video with the correct frame rate and size to speed up the process
        render_temp_path = os.path.join(RENDER_TEMPS_PATH, "render_temp.mkv")
        yield "Rescaling video... (application may become unresponsive)"
        ffmpeg_convert_cmd = (
            f'ffmpeg -i "{source_path}" -c:v ffv1 '
            + f'-vf "fps={frame_rate}, scale={size[0]}:{size[1]}" '
            + f'"{render_temp_path}"'
        )
        try:
            subprocess.run(ffmpeg_convert_cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise OSError("Could not convert video") from e
        # rendering the actual video from the temporary one
        with mpy.VideoFileClip(render_temp_path) as video:
            audio = video.audio
            video_duration = video.duration
            try:
                with open(dest_path, "wb") as wf:
                    video_frame_count = 0
                    audio_frame_count = 0
                    audio_written_bytes = 0
                    font_bytes = font.to_bytes()
                    # font_bytes_len
                    wf.write(len(font_bytes).to_bytes(INT_BYTES))
                    # font_bytes
                    wf.write(font_bytes)
                    # video_frame_rate
                    wf.write(frame_rate.to_bytes(INT_BYTES))
                    # video_frame_shape[0] (width)
                    wf.write(size[1].to_bytes(INT_BYTES))
                    # video_frame_shape[1] (height)
                    wf.write(size[0].to_bytes(INT_BYTES))
                    # # skipping INT_BYTES bytes for video_frame_count (will be written later)
                    video_count_pos = wf.tell()
                    wf.seek(video_count_pos + INT_BYTES)
                    # if video has audio and render_audio is True
                    if audio is not None and render_audio:
                        # audio_frame_rate
                        wf.write(audio.fps.to_bytes(INT_BYTES))
                        # audio_channel_count
                        wf.write(audio.nchannels.to_bytes(INT_BYTES))
                        audio_segment_size = (
                            audio.fps * audio.nchannels * AUDIO_BYTES_PER_SAMPLE
                        )
                        # skipping INT_BYTES bytes for audio_segment_count (will be written later)
                        audio_count_pos = wf.tell()
                        wf.seek(audio_count_pos + INT_BYTES)
                        # rendering all of the audio segments and padding them so
                        # that the total size is divisible by audio_segment_size
                        # (written in ~1s chunks)
                        for audio_chunk in audio.iter_chunks(
                            chunk_duration=1,
                            nbytes=AUDIO_BYTES_PER_SAMPLE,
                            quantize=True,
                        ):
                            audio_chunk_bytes = audio_chunk.tobytes()
                            wf.write(audio_chunk_bytes)
                            audio_written_bytes += len(audio_chunk_bytes)
                            audio_frame_count += 1
                            progress = round(
                                audio_written_bytes
                                / audio_segment_size
                                / video_duration
                                * 100,
                                2,
                            )
                            yield f"Rendering audio: {progress}%"
                        # padding
                        wf.write(
                            b"\x00"
                            * (
                                audio_segment_size
                                - (audio_written_bytes % audio_segment_size)
                            )
                        )
                        # returning to audio_segment_count and writing the value
                        # then returning back to the current end of the file
                        original_pos = wf.tell()
                        wf.seek(audio_count_pos)
                        wf.write((audio_frame_count).to_bytes(INT_BYTES))
                        wf.seek(original_pos)
                    # if video doesn't have audio or render_audio is False
                    else:
                        # audio_frame_rate (placeholder)
                        wf.write((0).to_bytes(INT_BYTES))
                        # audio_channel_count (placeholder)
                        wf.write((0).to_bytes(INT_BYTES))
                        # audio_segment_count (placeholder)
                        wf.write((0).to_bytes(INT_BYTES))
                    # all of the video frames
                    for frame in video.iter_frames():
                        char_image = CharImage(frame, 1, font)
                        image_chars_bytes = char_image.chars_to_bytes()
                        wf.write(image_chars_bytes)
                        video_frame_count += 1
                        progress = round(
                            video_frame_count / frame_rate / video.duration * 100, 2
                        )
                        yield f"Rendering video: {progress}%"
                    # returning to video_frame_count position and writing the value
                    wf.seek(video_count_pos)
                    wf.write(video_frame_count.to_bytes(INT_BYTES))
            except OSError as e:
                raise OSError(f"Could not save CharVideo to '{dest_path}'") from e
            video.close()
            os.remove(render_temp_path)
            yield f"Finished rendering '{dest_path.split('/')[-1]}' in {round(time.time() - t, 2)}s"
            return CharVideo(dest_path)

    def get_frame(self, frame: int) -> CharImage:
        """
        Gets the specified frame from the video.
        Last frame if frame would be OOB.
        """
        if frame >= self.video_frame_count:
            frame = self.video_frame_count - 1
        self.data_stream.seek(self.video_offset + frame * self.video_frame_size)
        image_chars = CharImage.chars_from_bytes(
            self.data_stream.read(self.video_frame_size), self.video_frame_shape
        )
        return CharImage(image_chars, 1, self.font)

    def get_audio_segment(self, segment_number: int) -> pygame.mixer.Sound:
        """
        Returns the specified second of audio from the video.
        Return blank audio if segment would be OOB.
        """
        self.data_stream.seek(
            self.audio_offset + segment_number * self.audio_segment_size
        )
        audio_bytes = self.data_stream.read(self.audio_segment_size)
        sound_array = np.frombuffer(audio_bytes, dtype=np.int16).reshape(
            -1, self.audio_channel_count
        )
        # adjusting the audio array to match the number of audio channels in pygame.mixer
        if pygame.mixer.get_init()[2] > 1:
            sound_array = np.repeat(
                sound_array,
                pygame.mixer.get_init()[2] // self.audio_channel_count,
                axis=1,
            )
        else:
            sound_array = sound_array[:, 0].copy("C")
        return pygame.sndarray.make_sound(sound_array)
