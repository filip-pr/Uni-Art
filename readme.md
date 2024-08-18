# Uni-Art

A program I created as a semester project at a university.

Allows for conversion of almost any image/video type to a corresponding data type made only out of Unicode characters and of course their playback.

Uni-Art allows for a great deal of customization, you can:

- Specify the set of characters to be used for conversion
- Set font in which the image or video will be rendered (and made to match the best)
- Toggle font features like ligatures and kerning
- Change the text and background colors
- Specifying number of characters an image or a video frame should have
- And more...

Uni-Art player is also able to render and play videos in real time. The performance largely depends on what hardware you're running it on, but even with a couple years old mid-range system one can render ~5000 character per frame video in 30fps without lag with monospace font and about ~1000 character per frame video in 30fps without lag with non-monospace (querying for non-monospace fonts can't be parallelized as well).

Please note that only operating system this was tested on is Windows 10 (with python 3.11.3) and there is no guarantee of it running anywhere else. Although in theory there shouldn't be a reason for it not to (at least not one that I'm aware of).

## Installation

To run Uni-Art one needs some non-standard libraries. To install those simply use:
- pip install -r requirements.txt

You might also need to install ffmpeg:
- https://ffmpeg.org/

## User guide

### Running of the program
Simply clone the repository, setup a python virtual environment and install the dependencies.

#### Running with GUI
Run gui.py. That should open your browser with the GUI which itself is pretty self-explanatory (if you really need there is hints button). Also please be patient and don't spam buttons as the multithreaded nature (and the fact that this is my first time working with anything of that sort) can make the app a little buggy. GUI itself was tested on Google Chrome and should work on any Chromium based browser.

#### Disclaimer
Even though the GUI app (gui.py) is technically a web server it is NOT EVER meant to be run any other way than locally. There is at least one pretty big security vulnerability (sending any file from the server to the client by just passing the file path as 'Other font path') and there likely are more. I only used flask as a convenient (although not as much as I first thought) way to use browser text rendering engine to render whatever text and font I wanted. 

#### Running in console
Run console.py with desired arguments:
- `-m or --mode`, choose the output, either file or terminal (required)
- `-s or --media-source`, path to used media file (required)
- `-f or --font-source`, path to used font (required)
- `--charset`, charset, either unicode, ascii or string of allowed characters(default=unicode)
- `--text-color`, text color in #RRGGBB format (default=#000000)
- `--background-color`, background color in #RRGGBB format (default=#FFFFFF)
- `--color`, if present, embedded color will be used
- `--kerning`, if present, kerning will be used
- `--ligatures`, if present, ligatures will be used 
- `--monospace`, if present, font will be force monospace
- `--font-size`, font render size (default=100)
- `--char-count`, desired approximate char count (required)
- `--row-spacing`, row spacing scale (default=1.0)
- `--distance-metric`, distance metric to be used, either manhattan or euclidean (default=manhattan)
- `--frame-rate`, video frame rate (default=30)
- `--chunk-length`, video chunk length (only used for rendering, higher values might improve render time) (default=5)
- `--buffer-size`, video frame buffer length (only used for rendering, higher values might improve render time) (default=100)
- `-d or --destination` destination file (only for file mode), if none is provided the result will be \<source file name>.txt


### Possible issues

#### Error setting font: invalid pixel size
This happens when the font you selected is incompatible with font render size you selected, (it is raised by PIL) so the best thing you can do is try search for 'python PIL \<font name> invalid pixel size' to find the right size or change to a different font. If you are using Google Noto Emoji the right size should be 109.

#### Video is lagging
Try lowering the character count, changing font or even forcing font monospace (will not work for all fonts). If forcing font monospace deforms the image (too much) you can try to specify charset and leaving out thin characters like dots and slashes.

#### Image or video has weird artifacts
From my experience this is only noticeable on black and white or other high contrast media. This is likely caused by video down-scaling for faster rendering, things that could help are choosing higher quality original or increasing he character count, reducing the charset by allowing only most matching characters can also help.

#### Image or video has wrong and/or shifted colors
This is more a feature rather than a bug. It is caused by color normalization. Without it the image quality would be quite a bit worse and lots of not so similar colors would show as the same character making the image unrecognizable.

#### Turning ligatures on deforms the image/video
This is caused by the fact that not all ligatures supported by the font are actually supported by the browser. There is really nothing one can do about that so they are turned off by default. When they are turned off hair space is inserted after each so accidental creation of ligatures is prevented.

## Save file formats

### Text image
- Magic number 157450653 (4 byte big-endian integer)
- Image text (UTF-8 encoded string)

### Text video
- Magic number 94987465 (4 byte big-endian integer)
- Video frame rate (4 byte big-endian integer)
- Video frame count (4 byte big-endian integer)
- Frame offset information for each frame
  - Frame offset (4 byte big-endian integer)
- Frame information for each frame
  - Frame size in bytes (4 byte big-endian integer)
  - Frame text (UTF-8 encoded string)
