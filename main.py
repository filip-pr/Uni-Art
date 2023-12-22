"""Main module for the application."""

import os

from tkinter import Tk

# Hide the pygame support prompt
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame

from arg_parser import parse_args
from gui import AppGUI
from font import Font
from char_image import CharImage


def main():
    """Main function for the application."""
    args = parse_args()
    if args.mode is None or args.mode == "gui":
        # GUI mode
        root = Tk()
        AppGUI(root)
        root.mainloop()
    pygame.init()
    pygame.display.set_mode(flags=pygame.HIDDEN)
    # Raise errors if required arguments are not specified
    if args.source is None:
        raise ValueError("Source must be specified")
    if args.charcount is None:
        raise ValueError("Character count must be specified")
    if args.fontname is None:
        raise ValueError("Font name must be specified")
    if args.fontsize is None:
        raise ValueError("Font size must be specified")
    font = Font(args.fontname, args.fontsize, args.bold, args.italic, args.charset)
    char_image = CharImage(args.source, args.charcount, font)
    if args.mode == "file":
        # File mode (only images are supported)
        if args.destination is None:
            raise ValueError("Destination must be specified")
        with open(args.destination, "w", encoding="utf-8") as fw:
            fw.write(char_image.chars_to_text())
    elif args.mode == "terminal":
        # Terminal mode (only images are supported)
        os.system("cls")
        print(char_image.chars_to_text())


if __name__ == "__main__":
    main()
