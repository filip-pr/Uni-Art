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
Run gui.py. That should open your browser with the GUI which itself is pretty self-explanatory (if you really need there is hints button). Also please be patient and don't spam buttons as the multithreaded nature (and the fact that this is my first time working with anything of that sort) can make the app a little buggy.

#### Disclaimer
Even though the GUI app (gui.py) is technically a web server it is NOT EVER meant to be run any other way than locally. There is at least one pretty big security vulnerability (sending any file from the server to the client by just passing the file path as 'Other font path') and there likely are more. I only used flask as a convenient (although not as much as I first thought) way to use browser text rendering engine to render whatever text and font I wanted. 


#### Running in console
Run console.py.


### Possible issues
- TODO

## Datatypes
- TODO
