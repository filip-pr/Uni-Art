"""Module containing the GUI of the application."""
import tkinter as tk
from tkinter import ttk
import tkinter.font
import tkinter.filedialog
import os

import pygame
from PIL import Image
import moviepy.editor as mpy

from font import Font
from char_image import CharImage
from char_video import CharVideo


class AppGUI:
    """Class representing the GUI of the application."""

    def __init__(self, master: tk.Tk) -> None:
        pygame.init()
        self.master = master
        self.font = None
        self.char_image = None
        self.char_video = None
        self.loaded_media_path = None
        self.loaded_media_type = None
        self.loaded_char_media_path = None
        self.loaded_char_media_type = None
        self.font_choices = list(filter(Font.name_exists, pygame.font.get_fonts()))

        # font menu variables
        self.font_name = tk.StringVar(self.master)
        self.font_size = tk.StringVar(self.master)
        self.font_bold = tk.BooleanVar(self.master)
        self.font_italic = tk.BooleanVar(self.master)
        self.add_char_set_input = tk.StringVar(self.master)
        self.char_set_ranges = []
        self.char_set_error = None

        # reading char_set_ranges.txt and handling errors
        try:
            current_line = 1
            with open("char_set_ranges.txt", "r", encoding="utf8") as rf:
                while True:
                    line = rf.readline().strip()
                    if line == "":
                        break
                    starting_value, char_set_name, char_set_ranges = line.split(":")
                    starting_value = bool(int(starting_value))
                    char_set_range_set = []
                    char_set_ranges = char_set_ranges.split(",")
                    for char_set_range in char_set_ranges:
                        start, end = list(
                            map(lambda x: int(x, 16), char_set_range.split("-"))
                        )
                        if not 0x0 <= start <= end <= 0x10FFFF:
                            raise ValueError()
                        char_set_range_set.append((start, end))
                    self.char_set_ranges.append(
                        [
                            char_set_name,
                            tk.BooleanVar(self.master, value=starting_value),
                            char_set_range_set,
                        ]
                    )
                    current_line += 1
        except (OSError, ValueError) as e:
            if isinstance(e, ValueError):
                self.char_set_error = (
                    f"Invalid entry in char_set_ranges.txt at line {str(current_line)}"
                )
            else:
                self.char_set_error = (
                    f"OSError while trying to read char_set_ranges.txt:\n{e}"
                )

        # video/image render menu variables
        self.render_input_path = tk.StringVar(self.master)
        self.render_dest_path = tk.StringVar(self.master)
        self.char_count = tk.StringVar(self.master)
        self.video_render_fps = tk.StringVar(self.master)
        self.video_render_audio = tk.BooleanVar(self.master)

        # char file menu variables
        self.char_file_path = tk.StringVar(self.master)
        self.char_video_start_time = tk.StringVar(self.master)

        # dynamic widgets
        self.font_info_label = None
        self.set_font_status_label = None

        self.render_file_info_label = None
        self.render_file_status_label = None

        self.render_status_label = None
        self.render_dest_path_button = None

        self.char_file_info_label = None
        self.char_file_status_label = None
        self.char_file_show_button = None
        self.char_file_play_status_label = None

        self._create_main_menu()

    def _create_main_menu(self):
        """Creates the main menu of the application."""

        # setting pygame window properties
        os.environ["SDL_VIDEO_CENTERED"] = "1"
        pygame.display.set_mode(flags=pygame.HIDDEN)
        pygame.display.set_caption("Uni-Art")
        pygame_icon = pygame.image.load("icon.ico")
        pygame.display.set_icon(pygame_icon)

        # setting tkinter window properties
        self.master.geometry("460x660")
        self.master.title("Uni-Art")
        self.master.iconbitmap("icon.ico")
        self.master.resizable(False, False)
        bg_color = "#EFEFEF"
        self.master.configure(background=bg_color)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", background=bg_color)
        style.configure("TLabel", background=bg_color)
        style.configure("TEntry", background=bg_color)
        style.configure("TCheckbutton", background=bg_color)
        style.configure("TMenubutton", background=bg_color)
        style.configure("TCombobox", background=bg_color)

        label_font = tkinter.font.Font(family="Arial", size=8)
        info_label_font = tkinter.font.Font(family="Arial", size=12, weight="bold")
        status_label_font = tkinter.font.Font(family="Arial", size=8, slant="italic")

        if self.char_set_error is not None:
            error_label = ttk.Label(text=self.char_set_error, font=label_font)
            error_label.grid(
                row=0,
                column=0,
                padx=10,
                pady=10,
            )
            return

        # font info label
        self.font_info_label = ttk.Label(
            text="Current font: None", font=info_label_font, width=48
        )
        self.font_info_label.grid(
            row=0, column=0, padx=10, pady=(2, 5), sticky="w", columnspan=5
        )

        # font name combobox
        font_name_label = ttk.Label(self.master, text="Font name", font=label_font)
        font_name_label.grid(row=1, column=0)

        font_name_dropdown = ttk.Combobox(
            self.master, values=self.font_choices, textvariable=self.font_name
        )
        font_name_dropdown.set(self.font_choices[0])
        font_name_dropdown.grid(row=2, column=0, padx=10)

        # font size input
        font_size_label = ttk.Label(self.master, text="Font size", font=label_font)
        font_size_label.grid(row=1, column=1)

        font_size_input = ttk.Entry(self.master, textvariable=self.font_size, width=7)
        self.font_size.set("12")
        font_size_input.grid(row=2, column=1, padx=10)

        # font bold checkbox
        font_bold_label = ttk.Label(self.master, text="Bold", font=label_font)
        font_bold_label.grid(row=1, column=2)

        font_bold_checkbox = ttk.Checkbutton(
            self.master, variable=self.font_bold, takefocus=False
        )
        font_bold_checkbox.grid(row=2, column=2, padx=10)

        # font italic checkbox
        font_italic_label = ttk.Label(self.master, text="Italic", font=label_font)
        font_italic_label.grid(row=1, column=3)

        font_italic_checkbox = ttk.Checkbutton(
            self.master, variable=self.font_italic, takefocus=False
        )
        font_italic_checkbox.grid(row=2, column=3, padx=10)

        # char set ranges menu
        char_set_ranges_label = ttk.Label(
            self.master, text="Char set ranges", font=label_font
        )
        char_set_ranges_label.grid(row=1, column=4)

        char_set_ranges_menu = ttk.Menubutton(self.master, text="Choose char sets")
        char_set_ranges_menu.menu = tk.Menu(char_set_ranges_menu, tearoff=0)
        for char_set in self.char_set_ranges:
            char_set_ranges_menu.menu.add_checkbutton(
                label=f"{char_set[0]}",
                variable=char_set[1],
                command=lambda: char_set_ranges_menu.menu.post(
                    char_set_ranges_menu.winfo_rootx(),
                    char_set_ranges_menu.winfo_rooty()
                    + char_set_ranges_menu.winfo_height(),
                ),
            )
        char_set_ranges_menu["menu"] = char_set_ranges_menu.menu
        char_set_ranges_menu.grid(row=2, column=4, padx=10)

        # font status label
        self.font_status_label = ttk.Label(self.master, font=status_label_font)
        self.font_status_label.grid(
            row=3, column=0, padx=10, pady=2, sticky="w", columnspan=5
        )

        # set font button
        set_font_button = ttk.Button(
            self.master,
            text="Set font",
            takefocus=False,
            command=self._set_font,
        )
        set_font_button.grid(row=4, column=0, padx=10, sticky="ew", columnspan=5)

        # file info label
        self.render_file_info_label = ttk.Label(
            text="Render source file: None", font=info_label_font, width=48
        )
        self.render_file_info_label.grid(
            row=5, column=0, padx=10, pady=(20, 5), sticky="w", columnspan=5
        )

        # file source path input
        render_source_file_path_label = ttk.Label(
            self.master, text="Image/Video file path", font=label_font
        )
        render_source_file_path_label.grid(row=6, column=0, columnspan=4)

        render_source_file_path_input = ttk.Entry(
            self.master, textvariable=self.render_input_path, state="readonly"
        )
        render_source_file_path_input.grid(
            row=7, column=0, padx=10, sticky="ew", columnspan=4
        )

        # file source path button
        render_source_file_path_button = ttk.Button(
            self.master,
            text="Browse",
            takefocus=False,
            command=lambda: [
                self.render_input_path.set(tkinter.filedialog.askopenfilename()),
                self._load_file(),
            ],
        )
        render_source_file_path_button.grid(row=7, column=4, sticky="ew", padx=10)

        # file status label
        self.render_file_status_label = ttk.Label(self.master, font=status_label_font)
        self.render_file_status_label.grid(
            row=8, column=0, padx=10, pady=2, sticky="w", columnspan=5
        )

        # render destination path input
        render_dest_path_label = ttk.Label(
            self.master, text="Render destination path", font=label_font
        )
        render_dest_path_label.grid(row=9, column=0, columnspan=4)

        render_dest_path_input = ttk.Entry(
            self.master, textvariable=self.render_dest_path, state="readonly"
        )
        render_dest_path_input.grid(
            row=10, column=0, padx=10, sticky="ew", columnspan=4
        )

        # render destination path button
        self.render_dest_path_button = ttk.Button(
            self.master,
            text="Browse",
            takefocus=False,
            state=tk.DISABLED,
            command=lambda: [
                self.render_dest_path.set(
                    tkinter.filedialog.asksaveasfilename(
                        defaultextension=".charim"
                        if self.loaded_media_type == "image"
                        else ".charvid",
                        filetypes=[
                            ("Char image", "*.charim")
                            if self.loaded_media_type == "image"
                            else ("Char video", "*.charvid")
                        ],
                        initialdir=self.render_input_path.get(),
                        initialfile=self.render_input_path.get()
                        .split("/")[-1]
                        .split(".")[0],
                    ),
                ),
            ],
        )
        self.render_dest_path_button.grid(row=10, column=4, sticky="ew", padx=10)

        # character count input
        char_count_label = ttk.Label(
            self.master, text="Character count", font=label_font
        )
        char_count_label.grid(row=11, column=0, padx=10)

        char_count_input = ttk.Entry(
            self.master, textvariable=self.char_count, width=14
        )
        self.char_count.set("10000")
        char_count_input.grid(row=12, column=0, padx=10)

        # video fps input
        video_fps_label = ttk.Label(self.master, text="Video FPS", font=label_font)
        video_fps_label.grid(row=11, column=1, padx=10)

        video_fps_input = ttk.Entry(
            self.master, textvariable=self.video_render_fps, width=7
        )
        self.video_render_fps.set("30")
        video_fps_input.grid(row=12, column=1, padx=10)

        # has audio checkbox
        render_audio_label = ttk.Label(self.master, text="Video audio", font=label_font)
        render_audio_label.grid(row=11, column=2, columnspan=2, padx=10)

        render_audio_checkbox = ttk.Checkbutton(
            self.master, variable=self.video_render_audio, takefocus=False
        )
        self.video_render_audio.set(True)
        render_audio_checkbox.grid(row=12, column=2, padx=10, columnspan=2)

        # render status label
        self.render_status_label = ttk.Label(self.master, font=status_label_font)
        self.render_status_label.grid(
            row=13, column=0, padx=10, pady=5, sticky="w", columnspan=5
        )

        # render file button
        render_char_file_button = ttk.Button(
            self.master,
            text="Render",
            takefocus=False,
            command=self._render_file,
        )
        render_char_file_button.grid(
            row=14, column=0, padx=10, sticky="ew", columnspan=5
        )

        # char file info label
        self.char_file_info_label = ttk.Label(
            text="Char file: None", font=info_label_font, width=48
        )
        self.char_file_info_label.grid(
            row=15, column=0, padx=10, pady=(20, 5), sticky="w", columnspan=5
        )

        # char file source path input
        char_file_path_label = ttk.Label(
            self.master, text="Char file file path", font=label_font
        )
        char_file_path_label.grid(row=16, column=0, columnspan=4)

        char_file_path_input = ttk.Entry(
            self.master, textvariable=self.char_file_path, state="readonly"
        )
        char_file_path_input.grid(row=17, column=0, padx=10, sticky="ew", columnspan=4)

        # char file source path button
        char_file_path_button = ttk.Button(
            self.master,
            text="Browse",
            takefocus=False,
            command=lambda: [
                self.char_file_path.set(
                    tkinter.filedialog.askopenfilename(
                        filetypes=[
                            ("Char image/video", ".charim .charvid"),
                        ],
                    )
                ),
                self._load_char_file(),
            ],
        )
        char_file_path_button.grid(row=17, column=4, sticky="ew", padx=10)

        # char file status label
        self.char_file_status_label = ttk.Label(self.master, font=status_label_font)
        self.char_file_status_label.grid(
            row=18, column=0, padx=10, pady=2, sticky="w", columnspan=5
        )

        # char video start time input
        char_video_start_time_label = ttk.Label(
            self.master, text="Char video start time (sec)", font=label_font
        )
        char_video_start_time_label.grid(row=19, column=0, padx=10)

        char_video_start_time_input = ttk.Entry(
            self.master, textvariable=self.char_video_start_time, width=14
        )
        self.char_video_start_time.set("0")
        char_video_start_time_input.grid(row=20, column=0, padx=10)

        # video player controls hint
        video_player_controls_label = ttk.Label(
            self.master,
            text="Controls:",
            font=label_font,
        )
        video_player_controls_label.grid(row=19, column=1, padx=10, columnspan=4)

        video_player_controls_hint_label = ttk.Label(
            self.master,
            text=(
                "C: Copy current frame to clipboard\n"
                + "SPACE (video): Start video and Pause/Unpause\n"
                + "Left/Right arrow (video): Rewind/Skip 10 seconds"
            ),
            font=label_font,
        )
        video_player_controls_hint_label.grid(row=20, column=1, padx=10, columnspan=4)

        # char file play status label
        self.char_file_play_status_label = ttk.Label(
            self.master, font=status_label_font
        )
        self.char_file_play_status_label.grid(
            row=21, column=0, padx=10, pady=5, sticky="w", columnspan=5
        )

        # char file show/play button
        self.char_file_show_button = ttk.Button(
            self.master,
            text="Show/Play",
            takefocus=False,
            state=tk.DISABLED,
            command=self._show_char_file,
        )
        self.char_file_show_button.grid(
            row=22, column=0, padx=10, sticky="ew", columnspan=5
        )

    def _show_char_file(self):
        """Shows a char image/video file in a pygame window."""
        if self.loaded_char_media_type == "image":
            self._show_char_image()
        else:
            try:
                if (
                    not 0
                    <= int(self.char_video_start_time.get())
                    <= self.char_video.duration
                ):
                    self.char_file_play_status_label.config(text="Invalid start time")
                    return
            except ValueError:
                self.char_file_play_status_label.config(text="Invalid start time")
                return
            start_time = int(self.char_video_start_time.get())
            self._play_char_video(start_time)

    def _show_char_image(self):
        """Displays a char image file in a pygame window."""
        self.master.withdraw()
        try:
            # scaling pygame display to fit the screen
            screen_info = pygame.display.Info()
            screen_resolution = (screen_info.current_w, screen_info.current_h)
            size = self.char_image.draw().get_size()
            width_ratio = (screen_resolution[0] * 0.9) / size[0]
            height_ratio = (screen_resolution[1] * 0.9) / size[1]
            scale_ratio = min(1, width_ratio, height_ratio)
            size = (int(size[0] * scale_ratio), int(size[1] * scale_ratio))
            screen = pygame.display.set_mode(size)
            clock = pygame.time.Clock()
            running = True
            while running:
                clock.tick(60)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break
                    # on c key press, copy the current frame to the clipboard
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                        self.master.clipboard_clear()
                        self.master.clipboard_append(
                            "\n".join(
                                [
                                    "".join(map(chr, row))
                                    for row in self.char_image.chars
                                ]
                            )
                        )
                image = self.char_image.draw()
                # scaling the image to fit the screen
                screen.blit(pygame.transform.scale(image, size), (0, 0))
                pygame.display.update()
            screen.fill((0, 0, 0))
            pygame.display.update()
        except (OSError, ValueError):
            self.char_file_play_status_label.config(
                text="Error while trying to show image"
            )
        pygame.display.set_mode(flags=pygame.HIDDEN)
        self.master.deiconify()

    def _play_char_video(self, start_time: int):
        """Plays a char video file in a pygame window.

        Args:
            start_time (int): Start time of the video in seconds.
        """
        self.master.withdraw()
        try:
            # scaling pygame display to fit the screen
            screen_info = pygame.display.Info()
            screen_resolution = (screen_info.current_w, screen_info.current_h)
            size = self.char_video.get_frame(0).draw().get_size()
            scale_ratio = min(
                1,
                (screen_resolution[0] * 0.9) / size[0],
                (screen_resolution[1] * 0.9) / size[1],
            )
            size = (int(size[0] * scale_ratio), int(size[1] * scale_ratio))
            screen = pygame.display.set_mode(size)
            frame = int(start_time) * self.char_video.video_frame_rate
            audio_segment = start_time
            audio_channel = pygame.mixer.Channel(0)
            clock = pygame.time.Clock()
            paused = True
            running = True
            while running:
                clock.tick(self.char_video.video_frame_rate)
                # handling pygame events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        audio_channel.stop()
                        paused = True
                        running = False
                        break
                    if event.type == pygame.KEYDOWN:
                        # on c key press, copy the current frame to the clipboard
                        if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                            self.master.clipboard_clear()
                            self.master.clipboard_append(
                                "\n".join(
                                    [
                                        "".join(map(chr, row))
                                        for row in self.char_video.get_frame(
                                            frame
                                        ).chars
                                    ]
                                )
                            )
                        # on space key press, pause/unpause the video
                        if event.key == pygame.K_SPACE:
                            paused = not paused
                            if paused:
                                audio_channel.pause()
                            else:
                                audio_channel.unpause()
                        # on left/right arrow key press, rewind/skip 10 seconds
                        elif event.key == pygame.K_LEFT:
                            audio_segment = max(0, audio_segment - 10)
                            frame = audio_segment * self.char_video.video_frame_rate
                            audio_channel.stop()
                        elif event.key == pygame.K_RIGHT:
                            audio_segment = min(
                                self.char_video.duration, audio_segment + 10
                            )
                            frame = audio_segment * self.char_video.video_frame_rate
                            audio_channel.stop()
                # handling audio
                if not paused and self.char_video.audio_channel_count:
                    if not audio_channel.get_busy():
                        audio_channel.play(
                            self.char_video.get_audio_segment(audio_segment)
                        )
                    if audio_channel.get_queue() is None:
                        frame = audio_segment * self.char_video.video_frame_rate
                        audio_segment += 1
                        audio_channel.queue(
                            self.char_video.get_audio_segment(audio_segment)
                        )
                # handling video
                image = self.char_video.get_frame(frame).draw()
                screen.blit(pygame.transform.scale(image, size), (0, 0))
                if not paused:
                    frame += 1
                # stopping the video when it reaches the end
                if frame >= self.char_video.video_frame_count:
                    paused = True
                    audio_channel.stop()
                pygame.display.update()
            screen.fill((0, 0, 0))
            pygame.display.update()
        except (OSError, ValueError):
            self.char_file_play_status_label.config(
                text="Error while trying to play video"
            )
        pygame.display.set_mode(flags=pygame.HIDDEN)
        self.master.deiconify()

    def _load_char_file(self):
        """Loads a char image/video file from the user's input."""
        path = self.char_file_path.get()
        if path == "":
            self.char_file_status_label.config(text="")
            return
        try:
            if path.endswith(".charim"):
                self.char_file_status_label.config(text="Char image file detected")
                self.char_image = CharImage.from_file(path)
                self.loaded_char_media_type = "image"
            elif path.endswith(".charvid"):
                self.char_file_status_label.config(text="Char video file detected")
                self.char_video = CharVideo(path)
                self.loaded_char_media_type = "video"
        except (OSError, ValueError):
            self.char_file_status_label.config(text="Unable to open selected file")
            return
        self.char_file_show_button.config(state=tk.NORMAL)
        self.char_file_info_label.config(text=f"Char file: {path.split('/')[-1]}")
        self.loaded_char_media_path = path

    def _render_file(self):
        """Renders a video/image file to a char image/video file."""
        if self.loaded_media_type is None:
            self.render_status_label.config(text="No source file selected")
            return
        if self.render_dest_path.get() == "":
            self.render_status_label.config(text="No render destination path set")
            return
        if self.loaded_media_type == "image":
            try:
                self.char_image = CharImage(
                    self.loaded_media_path, self.char_count.get(), self.font
                )
                self.char_image.as_file(self.render_dest_path.get())
                self.render_status_label.config(text="Image rendered successfully")
                self.loaded_char_media_type = "image"
                self.char_image = CharImage.from_file(self.render_dest_path.get())
            except (ValueError, OSError) as e:
                self.render_status_label.config(text=str(e))
                return
        else:
            try:
                for status in CharVideo.render(
                    self.loaded_media_path,
                    self.render_dest_path.get(),
                    self.char_count.get(),
                    self.video_render_fps.get(),
                    self.video_render_audio.get(),
                    self.font,
                ):
                    self.render_status_label.config(text=status)
                    self.master.update()
                self.loaded_char_media_type = "video"
                self.char_video = CharVideo(self.render_dest_path.get())
            except (ValueError, OSError) as e:
                self.render_status_label.config(text=str(e))
                return
        self.char_file_show_button.config(state=tk.NORMAL)
        self.loaded_char_media_path = self.render_dest_path.get()
        self.render_dest_path.set("")
        self.char_file_info_label.config(
            text=f"Char file: {self.loaded_char_media_path.split('/')[-1]}"
        )

    def _load_file(self):
        """Loads a video/image file from the user's input."""
        path = self.render_input_path.get()
        loaded_media = None
        if path == "":
            self.render_file_status_label.config(text="")
            return
        try:
            loaded_media = mpy.VideoFileClip(path)
        except OSError:
            pass
        try:
            loaded_media = Image.open(path)
        except OSError:
            pass
        if loaded_media is None:
            self.render_file_status_label.config(text="Unable to open selected file")
            return
        if isinstance(loaded_media, mpy.VideoFileClip):
            self.render_file_status_label.config(text="Video file detected")
            self.loaded_media_type = "video"
        else:
            self.render_file_status_label.config(text="Image file detected")
            self.loaded_media_type = "image"
        self.render_file_info_label.config(
            text=f"Render source file: {path.split('/')[-1]}"
        )
        self.render_dest_path_button.config(state=tk.NORMAL)
        self.loaded_media_path = path

    def _set_font(self):
        """Sets the selected font."""
        try:
            char_set = set()
            for char_range in self.char_set_ranges:
                if char_range[1].get():
                    for char_set_range_set in char_range[2]:
                        start, end = char_set_range_set
                        for char in range(start, end + 1):
                            char_set.add(char)
            self.font = Font(
                self.font_name.get(),
                self.font_size.get(),
                self.font_bold.get(),
                self.font_italic.get(),
                char_set,
            )
        except ValueError as e:
            self.font_status_label.config(text=str(e))
            return
        self.font_status_label.config(text="Font set successfully")
        self.font_info_label.config(
            text=(
                f"Current font: {'bold ' if self.font.font.get_bold() else ''}"
                + f"{'italic ' if self.font.font.get_italic() else ''}"
                + f"{self.font.name} size {self.font.font_size} "
                + f"({len(self.font.char_dict)} characters)"
            )
        )
