# Uni-Art

A program I created as a semester project at a university.

Allows for conversion of almost any image/video type to a corresponding data type made only out of Unicode characters and of course their playback (video player also supports audio).

Uni-Art allows for a great deal of customization like:

- Set of characters to be used for conversion
- Font in which the image or video will be rendered (and made to match the best)
- Specifying number of characters an image or a video frame should have
- And more..

Please note that only operating system this was tested on is Windows 10 and there is no guarantee of it running anywhere else. Although in theory there shouldn't be a reason for it not to (at least not one that I'm aware of).

## Installation

To run Uni-Art one needs some non-standard libraries. To install those simply use:
- `pip install numpy`
- `pip install scipy`
- `pip install pillow`
- `pip install pygame`
- `pip install moviepy`

## User guide

### Running of the program
After the installation everything is quite simple, just put all the files from this repository into a folder and run `main.py`.
A window named Uni-Art should appear, from there it should be quite straight forward. Just set you font, choose an image or a video you want to convert,
choose the destination, character count and in case of video conversion the FPS and whether the converted video should have the original audio. After that simply click render and once the rendering is done click the Show/Play button. If you already have a converted file and you just want to play it, just select it and click Show/Play.

### Possible issues
`Image or video has distorted characters or weird artifacts on the screen:`
- Lower the font size a bit, it might need some experimentation. This is caused due to downscaling of the rendered image that would be too big to fit on screen otherwise


`Video is lagging/skipping frames/too slow:`
- Decrease the video FPS or the character count. This is caused due to pygame not being able to handle rendering all the characters in the desired frame rate.

### Configuring of char_set_ranges.txt
To add custom character ranges as character sets one must add lines to the char_set_ranges.txt. All the lines must be in format:

- `default value`:`range name`:`range start`-`range end`

`default value` should be 1 if the range should be selected by default else 0

`range name` can be whatever string representing the name of the range (cannot include `:` for obvious reasons)

`range start` and `range end` must be hexadecimal numbers that satisfy `0x0`≤`range start`≤`range end`≤`0x10FFFF`

## .charim and .charvid datatypes

### Used datatypes information
- `int` is a 4 byte unsigned integer in big endian ordering
- `string` is a varying length string encoded in utf-8
- `bool` is a 1 byte value representing a boolean
- `unicode char bytes` is a 3 bit unsigned integer value in big endian ordering representing a Unicode character index
- `audio channel sample` is a signed 2 byte integer in big endian ordering

### Font bytes
Font bytes `font_bytes` are in following format:
- `font_name_bytes_length` - `int` representing byte length of font name
- `font_name_bytes` - `string` containing the font name
- `font_size` - `int` representing the font size
- `bold` - `bool` representing whether the font is bold or not
- `italic` - `bool` representing whether the font is italic or not
- `char_set_length` - `int` representing how many characters does its char set have
- `char_set_bytes` - `char_set_length` * `int` each `int` representing a single character in char set

### .charim
.charim file is in following format:
- `font_bytes_length` - `int` representing the number of bytes the image's `font_bytes` have
- `font_bytes` - `font_bytes` of the image's font
- `rows` - `int` representing height of the image (in characters)
- `columns` - `int` representing width of the image (in characters)
- `char_image_bytes` - (`rows` * `unicode char bytes`) * `columns` representing characters at each position of rendered image

### .charvid
- `font_bytes_length` - `int` representing the number of bytes the video's `font_bytes` have
- `font_bytes` - `font_bytes` of the video's font
- `video_frame_rate` - `int` representing frame rate of the rendered video
- `video_frame_width` - `int` representing width of each frame (in characters)
- `video_frame_height` - `int` representing height of each frame (in characters)
- `video_frame_count` - `int` representing the number of frames the rendered video has
- `audio_sample_rate` - `int` representing the audio sample rate
- `audio_channel_count` - `int` representing the number of audio channels the audio track of the rendered video has
- `audio_segment_count` - `int` representing the number of 1s audio segments the audio track of the rendered video has
- `audio_segments` - [(`audio_channel_count` * `audio channel sample`) * `audio_sample_rate`] * `audio_segment_count` representing 1s audio segments of the rendered video's audio track
- `video_frames` - [(`video_frame_width` * `unicode char bytes`) * `video_frame_height`] * `video_frame_count` representing rendered video's frames
  
