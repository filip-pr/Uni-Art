# UNI-ART Documentation

## About
This document contains the description of the inner workings of Uni-Art project.

## Modules

### font.py
`font.py` module contains the class Font used for rendering and analyzing font, allowing some customization. It is mainly based on the `pygame.font` module and `pygame.freetype` module. It stores pixel data for each glyph in the font, along with each glyphs color average used in combination with `scipy`'s spatial.KDTree for fast color to glyph queries. All glyph color averages are normalized for the sake of having a more detailed image.

### char_image.py
`char_image.py` module contains the CharImage class used to represent and render unicode art images. It uses `PIL`'s Image to load and process images. Each image is created by simply resizing it to a calculated size (so it has around the number of desired characters and somewhat preserves the aspect ratio) and then taking each pixel color value and querying for the closest matching character. Also allows for storage of the image in a custom data format more described in `README.md`.

### char_video.py
`char_video.py` module contains the CharVideo class used to represent and render videos as series of CharImage images. It uses the `moviepy` module and `ffmpeg` to load and process videos. CharVideo also allows for sound storage along with it. The videos have to be rendered before displaying them first (it is possible to render in realtime, but maybe in a future update), the format which they are rendered to is described more in detail in `README.md` file. The rendering is done in 3 stages. First stage is simply rescaling the video to desired size and fps using ffmpeg (stored as a temporary file in the program directory). The second stage is optional, audio gets saved. The third stage is converting individual video frames to `image arrays` which are arrays of 3 byte values representing unicode code points for each character.

### gui.py
`gui.py` module simply contains things regarding the GUI. It mainly uses two graphics libraries, `Tkinter` and `PyGame`. `Tkinter` is used for the settings interface (since it allows for easy creation of buttons and other elements), while `PyGame` is used for rendering CharImages and CharVideos (since it is much more performant and easy to do exactly what is necessary).

### consts.py
`consts.py` module contains constants used throughout the project, making things (hopefully) more clear.

### arg_parser.py
`arg_parser.py` module contains a function that parses command line arguments. It uses the `argparse` module.  The arguments themselves and their use cases are explained in `README.md`.

### main.py
`main.py` module is the main module of the application, nothing more, nothing less.

