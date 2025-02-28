# 1. VOC2CORE

## 1.1. Contents

<!-- TOC -->

- [1.1. Contents](#11-contents)
- [1.2. Purpose](#12-purpose)
- [1.3. Features](#13-features)
- [1.4. Installation](#14-installation)
  - [1.4.1. Debian / Ubuntu](#141-debian--ubuntu)
  - [1.4.2. Requirements](#142-requirements)
  - [1.4.3. For vaapi en/decoding](#143-for-vaapi-endecoding)
  - [1.4.4. Optional for the Example-Scripts](#144-optional-for-the-example-scripts)
- [1.5. Debugging](#15-debugging)
- [1.6. Mixing Pipeline](#16-mixing-pipeline)
  - [1.6.1. Input Elements](#161-input-elements)
    - [1.6.1.1. Sources](#1611-sources)
      - [1.6.1.1.1. Test Sources](#16111-test-sources)
      - [1.6.1.1.2. TCP Sources](#16112-tcp-sources)
      - [1.6.1.1.3. File Sources](#16113-file-sources)
      - [1.6.1.1.4. Decklink Sources](#16114-decklink-sources)
      - [1.6.1.1.5. Image Sources](#16115-image-sources)
      - [1.6.1.1.6. Video4Linux2 Sources](#16116-video4linux2-sources)
      - [1.6.1.1.7. AJA Sources](#16117-aja-sources)
      - [1.6.1.1.8. Common Source Attributes](#16118-common-source-attributes)
    - [1.6.1.2. Background Video Source](#1612-background-video-source)
      - [1.6.1.2.1. Multiple Background Video Sources (depending on Composite)](#16121-multiple-background-video-sources-depending-on-composite)
    - [1.6.1.3. Blinding Sources (Video and Audio)](#1613-blinding-sources-video-and-audio)
      - [1.6.1.3.1. A/V Blinding Source](#16131-av-blinding-source)
      - [1.6.1.3.2. Separated Audio and Video Blinding Source](#16132-separated-audio-and-video-blinding-source)
    - [1.6.1.4. Overlay Sources](#1614-overlay-sources)
      - [1.6.1.4.1. Single Overlay Image File](#16141-single-overlay-image-file)
      - [1.6.1.4.2. Multiple Overlay Image Files](#16142-multiple-overlay-image-files)
      - [1.6.1.4.3. Select Overlays from a Schedule](#16143-select-overlays-from-a-schedule)
        - [1.6.1.4.3.1. Filtering Events](#161431-filtering-events)
      - [1.6.1.4.4. Additional Overlay Options](#16144-additional-overlay-options)
        - [1.6.1.4.4.1. Auto-Off](#161441-auto-off)
  - [1.6.2. Output Elements](#162-output-elements)
    - [1.6.2.1. Mix Live](#1621-mix-live)
    - [1.6.2.2. Mix Recording](#1622-mix-recording)
    - [1.6.2.3. Mix Preview](#1623-mix-preview)
    - [1.6.2.4. Sources Live](#1624-sources-live)
    - [1.6.2.5. Sources Recording](#1625-sources-recording)
    - [1.6.2.6. Sources Preview](#1626-sources-preview)
    - [1.6.2.7. Mirror Ports](#1627-mirror-ports)
    - [1.6.2.8. SRT Server](#1628-srt-server)
    - [1.6.2.9. Program Output](#1629-program-output)
      - [1.6.2.9.1. AJA Program Output](#16291-aja-program-output)
  - [1.6.3. A/V Processing Elements](#163-av-processing-elements)
    - [1.6.3.1. DeMux](#1631-demux)
    - [1.6.3.2. Mux](#1632-mux)
  - [1.6.4. Video Processing Elements](#164-video-processing-elements)
    - [1.6.4.1. Scale](#1641-scale)
    - [1.6.4.2. Mix Compositor](#1642-mix-compositor)
    - [1.6.4.3. Mix Blinding Compositor](#1643-mix-blinding-compositor)
    - [1.6.4.4. Sources Blinding Compositor](#1644-sources-blinding-compositor)
  - [1.6.5. Audio Processing Elements](#165-audio-processing-elements)
    - [1.6.5.1. Audio Mixer](#1651-audio-mixer)
    - [1.6.5.2. Audio Blinding Mixer](#1652-audio-blinding-mixer)
  - [1.6.6. Live Sources](#166-live-sources)
- [1.7. Decoder and Encoder](#17-decoder-and-encoder)
  - [1.7.1. CPU](#171-cpu)
  - [1.7.2. VAAPI](#172-vaapi)

<!-- /TOC -->

## 1.2. Purpose

**VOC2CORE** is a server written in python which listens at port `9999` for incoming TCP connections to provide a command line interface to manipulate a [GStreamer](http://gstreamer.freedesktop.org/) pipeline it runs.
The gstreamer pipeline is meant to mix several incoming video and audio sources to different output sources.

Particularly it can be used to send mixtures of the incoming video and audio sources to a live audience and/or to a recording server.

**VOC2CORE** can be easily adapted to different scenarios by changing it's configuration.

One can use a simple terminal connection to control the mixing process or **VOC2GUI** which provides a visual interface that shows previews of all sources and the mixed output as well as a toolbar for all mixing commands.

## 1.3. Features

**VOC2CORE** currently provides the following features:

* [Matroska](http://www.matroska.org/) enveloped A/V source input via TCP
* Image sources via URI
* [Decklink](https://www.blackmagicdesign.com/products/decklink) grabbed A/V sources
* Video4Linux2 video sources
* GStreamer generated test sources
* [Matroska](http://www.matroska.org/) enveloped A/V output via TCP
* Scaling of input sources to the desired output format
* Conversion of input formats to the desired output format
* Composition of video sources to a mixed video output (e.g. Picture in Picture)
* Blinding of mixed video and audio output (formerly known as "stream blanking", e.g. to interrupt live streaming between talks)
* Low resolution preview outputs of sources and mix for lower bandwidth monitoring
* High resolution outputs of sources and mix for high quality recording
* Remote controlling via command line interface
* Video transitions for fading any cuts
* Image overlays (e.g. for lower thirds)
* Reading a so-called [`schedule.xml`](https://github.com/voc/voctosched) which can provide meta data about the talks and that is used to address images individually for each talk that can be selected as overlay (e.g. speaker descriptions in lower thirds)
* Customization of video composites and transitions

## 1.4. Installation

Currently, voc2mix is only works on linux based operating systems. It is tested on ubuntu 20.04 as well
as debian buster and bullseye. It will probably work on most linux distributions which can satisfy the dependencies below.
Voc2mix can run on Gstreamer version < 1.8 but at least 1.14 is recommended.

### 1.4.1. Debian / Ubuntu

On Ubuntu 18.04 to 20.04 and Debian buster/bullseye the following packages are needed. The python dependencies can also be handled in a venv.
Both Debian and Ubuntu provide voctomix packages which my or may not be outdated. Currently, its recommended to check out voc2mix from the git repository.

````bash
git clone https://github.com/voc/voctomix.git
git checkout voctomix2
````

### 1.4.2. Requirements

````bash
sudo apt install gstreamer1.0-plugins-bad gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly gstreamer1.0-tools libgstreamer1.0-0 gstreamer1.0-x python3 python3-gi gir1.2-gstreamer-1.0 gir1.2-gst-plugins-base-1.0 python3-sdnotify python3-scipy gstreamer1.0-gl gstreamer1.0-pulseaudio
````

### 1.4.3. For vaapi en/decoding

````bash
sudo apt install gstreamer1.0-vaapi
````

### 1.4.4. Optional for the Example-Scripts

````bash
sudo apt install python3-pyinotify gstreamer1.0-libav rlwrap fbset ffmpeg netcat
````

## 1.5. Debugging

Here are some debugging tips:

* Use option `-v`, `-vv` or `-vvv` to set more and more verbose logging from **VOC2CORE**.
* Use option `-g`, `-gg` to set more and more verbose logging from GStreamer.
* Use option `-p` to generate file including string of pipeline that **VOC2CORE** is about to create.
* Use option `-d` to generate DOT graphs of the GStreamer pipeline that **VOC2CORE** has created.
* Use option `-D` to generate DOT graphs like with `-d` but set detail level of DOT graph.
* DOT graph files can be viewed with `xdot` for example.

## 1.6. Mixing Pipeline

The following graph shows a simplified mixing pipeline.
The real GStreamer pipeline is much more complicated.
A so-called [DOT graph](https://www.graphviz.org/) of it can be generated by starting **VOC2CORE** with option `-d`. Those DOT graph files can be viewed with [xdot](https://github.com/jrfonseca/xdot.py) for example.

![**VOC2CORE** Mixing Pipeline](images/pipelines.svg)

### 1.6.1. Input Elements

#### 1.6.1.1. Sources

Live audio/video input can be delivered in different *kinds* via **TCP** in **Matroska format** or from a **Decklink capture card** source. **Video4Linux2** devices can also be used as video only sources. It is also possible to use **image** and **test** sources, but this mostly make sense for testing purposes.

All input sources must be named uniquely and listed in `mix/sources` within the configuration file:

```ini
[mix]
sources = cam1,cam2
```

Without any further configuration this will produce two test sources named `cam1` and `cam2`.

##### 1.6.1.1.1. Test Sources

Without any further configuration a source becomes a **test source** by default.
Every test source will add a [videotestsrc](https://gstreamer.freedesktop.org/documentation/videotestsrc/index.html?gi-language=python) and an [audiotestsrc](https://gstreamer.freedesktop.org/documentation/audiotestsrc/index.html?gi-language=python) element to the internal GStreamer pipeline and so it produces a test video and sound.
As in the order they appear in `mix/sources` the test patterns of all test sources will iterate through the following values:

`smpte`, `ball`, `red`, `green`, `blue`, `black`, `white`, `checkers-1`, `checkers-2`, `checkers-4`, `checkers-8`, `circular`, `blink`, `smpte75`, `zone-plate`, `gamut`, `chroma-zone-plate`, `solid-color`, `smpte100`, `bar`, `snow`, `pinwheel`, `spokes`, `gradient`, `colors`

You can also set a specific audio pattern by setting `mix/wave` to one the following types:

`sine`, `square`, `saw`, `triangle`, `silence`, `white-noise`, `pink-noise`, `sine-table`, `ticks`, `gaussian-noise`, `red-noise`, `blue-noise`, `violet-noise`,

The default is `sine`, with a frequency of 1kHz at -18dbFS.

To set the pattern of a test source explicitly you need to add an own section `source.x` (where `x` is the source's identifier) to the configuration

```ini
[mix]
sources = cam1,cam2

[source.cam1]
pattern = ball
wave = white-noise
```

Now source `cam1` will show a moving white ball on black background instead of a *SMPTE* pattern signal and play white noise instead of a sine.

To change the *kind* of a source you need to set the `kind` attribute in the source's configuration section as described in the following paragraphs.

##### 1.6.1.1.2. TCP Sources

You can use `tcp` as a source's `kind` if you would like to provide Matroska A/V streams via TCP.
**TCP sources** will be assigned to port `16000` and the following in the order in which they appear in `mix/sources`.

```ini
[mix]
sources = cam1,cam2

[source.cam1]
kind = tcp

[source.cam2]
kind = tcp
```

This configuration let VOC2CORE listen at port `16000` for an incoming TCP connection transporting a Matroska A/V stream for source `cam1` and at port `16001` for source `cam2`.

##### 1.6.1.1.3. File Sources

You can use `file` as a source's `kind` if you would like to provide a file that will be played e.g. to provide a blinder animation. Setting the loop property to `false` is not useful at this point.

Currently, file sources are expected to be MPEG TS containers with MPEG-2 Video and MP2 or MP3 audio. Support of further container, audio and video types may be supported in future releases

```ini
[source.blinder]
kind=file
location=/path/to/pause.ts
loop=true
```

This configuration will loop pause.ts as the default blinder, using its audio and video

##### 1.6.1.1.4. Decklink Sources

You can use `decklink` as a source's `kind` if you would like to grab audio and video from a [Decklink](https://www.blackmagicdesign.com/products/decklink) grabber card.

```ini
[mix]
sources = cam1,cam2

[source.cam1]
kind = decklink
devicenumber = 1

[source.cam2]
kind = decklink
devicenumber = 3
```

You now have two **Decklink A/V grabber** sources at device number `1` for `cam1` and `3` for `cam2`.

Optional attributes of Decklink sources are:

| Attribute Name     | Example Values                                     | Default   | Description (follow link)
| ------------------ | -------------------------------------------------- | --------- | -----------------------------------------
| `devicenumber`     | `0`, `1`, `2`, ...                                 | `0`       | [Decklink `device-number`](https://gstreamer.freedesktop.org/documentation/decklink/decklinkvideosrc.html#decklinkvideosrc:device-number)
| `video_connection` | `auto`, `SDI`, `HDMI`, ...                         | `auto`    | [Decklink `connection`](https://gstreamer.freedesktop.org/documentation/decklink/decklinkvideosrc.html#GstDecklinkConnection)
| `video_mode`       | `auto`, `1080p25`, `1080i50`, ...                  | `auto`    | [Decklink `modes`](https://gstreamer.freedesktop.org/documentation/decklink/decklinkvideosrc.html#decklinkvideosrc_GstDecklinkModes)
| `video_format`     | `auto`, `8bit-YUV`, `10bit-YUV`, `8bit-ARGB`, ...  | `auto`    | [Decklink `video-format`](https://gstreamer.freedesktop.org/documentation/decklink/decklinkvideosrc.html#decklinkvideosrc_GstDecklinkVideoFormat)
| `audio_connection` | `auto`, `embedded`, `aes`, `analog`, `analog-xlr`, `analog-rca` | `auto`    | [Decklink `audio-connection`](https://gstreamer.freedesktop.org/documentation/decklink/decklinkaudiosrc.html#GstDecklinkAudioConnection)

##### 1.6.1.1.5. Image Sources

You can use `img` as a source's `kind` if you would like to generate a still video from an image file.

```ini
[mix]
sources = cam1,cam2

[source.cam1]
kind = img
imguri = http://domain.com/image.jpg

[source.cam2]
kind = img
file = /opt/voctomix/image.png
```

As you see you can use either `imguri` or `file` to select an image to use.

| Attribute Name     | Example Values                                     | Default   | Description
| ------------------ | -------------------------------------------------- | --------- | -----------------------------------------
| `imguri`           | `http://domain.com/image.jpg`                      | n/a       | use image from URI
| `file`             | `/opt/voctomix/image.png`                          | n/a       | use image from local file

##### 1.6.1.1.6. Video4Linux2 Sources

You can use `v4l2` as a source's `kind` if you would like to use video4linux2 devices as video input.
To get the supported video modes, resolution and framerate you can use ffprobe and ffplay.

```bash
ffprobe /dev/video0
```

```ini
[mix]
sources = cam1,cam2

[source.cam1]
kind=v4l2
device=/dev/video2
width=1280
height=720
framerate=10/1
format=YUY2

```

| Attribute Name     | Example Values                                     | Default     | Description
| ------------------ | -------------------------------------------------- | ----------- | -----------------------------------------
| `device`           | `/dev/video0`                                      | /dev/video0 | video4linux2 device to use
| `width`            | `1280`                                             | 1920        | video width expected from the source
| `height`           | `720`                                              | 1080        | video height expected from the source
| `framerate`        | `10/1`                                             | 25/1        | video frame rate expected from the source
| `format`           | `YUY2`                                             | YUY2        | video format expected from the source

##### 1.6.1.1.7. AJA Sources

You can use `aja` as a source's `kind` if you would like to grab audio and
video from a [AJA](https://www.aja.com/family/desktop-io) Desktop I/O grabber
card.

```ini
[mix]
sources = cam1,cam2

[source.cam1]
kind = aja
device = 00A00012
channel = 0

[source.cam2]
kind = aja
device = 00A00012
channel = 1
```

You now have two **AJA A/V grabber** sources, using input channels 0 and 1;
this usually maps to the first two SDI inputs.

The `device` attribute must be set, and is usually a truncated part of the
serial number. If set to `?`, then a list of discovered cards will be printed
at startup by libajantv2, and then voctocore will quit.

Optional attributes of AJA sources are:

| Attribute Name     | Example Values                                          | Default    | Description (follow link)
| ------------------ | ------------------------------------------------------- | ---------- | -----------------------------------------
| `device`           | `00A00012`, ...                                         | ``         | [AJA `device-identifier`](https://gstreamer.freedesktop.org/documentation/aja/ajasrc.html#ajasrc:device-identifier)
| `channel`          | `0`, `1`, `2`, ...                                      | `0`        | [AJA `channel`](https://gstreamer.freedesktop.org/documentation/aja/ajasrc.html#ajasrc:channel)
| `video_mode`       | `auto`, `1080p-2500`, `1080p-6000-a`, `1080i-5000`, ... | `auto`     | [AJA `video-format`](https://gstreamer.freedesktop.org/documentation/aja/ajasrc.html#GstAjaVideoFormat)
| `audio_source`     | `embedded`, `aes`, `analog`, `hdmi`, `mic`              | `embedded` | [AJA `audio-source`](https://gstreamer.freedesktop.org/documentation/aja/ajasrc.html#GstAjaAudioSource)

##### 1.6.1.1.8. Common Source Attributes

These attributes can be set for all *kinds* of sources:

| Attribute Name     | Example Values                                     | Default       | Description
| ------------------ | -------------------------------------------------- | ------------- | -----------------------------------------
| `scan`             | `progressive`, `interlaced`, `psf`                 | `progressive` | select video mode (`psf` = Progressive segmented frame)
| `volume`           | `0.0`, ..., `1.0`                                  | `0.0`         | audio volume (if reasonable)

#### 1.6.1.2. Background Video Source

The `background` source is *obligatory* and does not have to be listed in `mix/sources`.
The background source will be placed on bottom (z-order) of the video mix.
By default the background source is a `black` video test source.
Yout need to configure the background source (as any other) if you want to change that:

```ini
[source.background]
kind=img
file=bg.png
```

The background source is **video only** and so any audio sources will be ignored.

##### 1.6.1.2.1. Multiple Background Video Sources (depending on Composite)

You may also have multiple backgrounds and attach them to your composites.
Often - for example - you have a logo in the background which needs to be shown on different places depending on where your composites leave unused space.

By configuring a list of background sources in `mix`/`backgrounds` you can configure every single one of them.
The default background source called `background` wont be used then.

```ini
[mix]
backgrounds=background1,background2

[source.background1]
kind=img
file=bg.png
composites=fs

[source.background2]
kind=test
pattern=black
composites=sbs,pip
```

To control when the backgrounds will be used just add a list of `composites` to your source configuration.
The core then will search for backgrounds that match the current composite and cut or fade them when composites are switched.

#### 1.6.1.3. Blinding Sources (Video and Audio)

The blinder (fka stream-blanker) blinds all live outputs.
You can activate the blinder in the configuration like that:

```ini
[blinder]
enable=true
```

By default the blinder generates a Gstreamer test source which shows a SMPTE pattern.
But you have several options to define your own blinder sources:

##### 1.6.1.3.1. A/V Blinding Source

If you like to set up a custom blinding source you have to configure a source that is named `blinder`:

```ini
[blinder]
enable=true

[source.blinder]
kind=test
pattern=black
volume=0.0
```

This would define a blinder source that is a black screen with silent audio.
But you can use any other source kind too.

##### 1.6.1.3.2. Separated Audio and Video Blinding Source

Another way to define binding sources is to configure one audio source and one or more video sources.
The blinder then will blind with the one given audio source but you can select between different video sources.
This is useful if you want to have different video messages which you want to differ (for different day times for example, like having a break at lunch or end of the event or a trouble message.
If you want to do so, you have to define the audio source within the blinding source and add as many video blinding sources within the `blinder` section:

```ini
[blinder]
enable=true
videos=break,closed

[source.blinder]
kind=tcp

[source.break]
kind=tcp

[source.closed]
kind=tcp
```

This will listen at three different ports for the audio source, the break video source and the closed video source.

#### 1.6.1.4. Overlay Sources

Overlays are placed on top (z-order) of the video mix.
Currently they can be provided as bitmap images only.

These bitmap images will be loaded from the current working directory.
If you want to specify an image directory you can use the attribute `overlay`/`path`:

```ini
[overlay]
path = ./data/images/overlays
```

Now all images will be loaded from the folder `./data/images/overlays`.

You can configure which overlay images will be available for an insertion in three different ways selectively or in parallel.

##### 1.6.1.4.1. Single Overlay Image File

The simplest method is to set a single overlay file that will be displayed as overlay initially after the server starts:

```ini
[overlay]
file = watermark.png|Watermark Sign
```

The given file name can be followed by a `|` and a verbal description of the file's contents which substitutes the filename within selections in the user interface.

##### 1.6.1.4.2. Multiple Overlay Image Files

You can also list multiple files which then can be selected between by using the property `files`:

```ini
[overlay]
files = first.png|1st overlay, second.png|2nd overlay, third.png|3rd overlay
```

Same principle but a comma separated list of image names and descriptions.
The `files` attribute will not activate an overlay at server start.

##### 1.6.1.4.3. Select Overlays from a Schedule

A more complex method is to configure a schedule file which is an XML file including information about one or multiple event schedules.
From these information **VOC2MIX** can generate file names in the form of `event_{eid}_person_{pid}.png` or `event_{eid}_persons.png` where `{eid}` and `{pid}` are placeholders for the event/id and person ID of the speakers of the event.
The first variant is used to address every single speaker and the second variant all participating persons at once.

Below you can see an example consisting of the necessary XML elements and by that describing three events and up to three speakers.  

```xml
<?xml version='1.0' encoding='utf-8' ?>
<schedule>
  <day>
    <room>
      <event id='1'>
        <date>2019-01-01T10:00:00+02:00</date>
        <duration>01:00</duration>
        <room>HALL 1</room>
        <title>Interesting talk in HALL 1 at 10:00</title>
        <persons>
          <person id='1'>Alice</person>
          <person id='2'>Bob</person>
          <person id='3'>Claire</person>
        </persons>
      </event>
      <event id='2'>
        <date>2019-01-01T10:00:00+02:00</date>
        <duration>01:00</duration>
        <room>HALL 2</room>
        <title>Interesting talk in HALL 2 at 10:00</title>
        <persons>
          <person id='4'>Dick</person>
        </persons>
      </event>
      <event id='3'>
        <date>2019-01-01T11:15:00+02:00</date>
        <duration>01:00</duration>
        <room>HALL 2</room>
        <title>Interesting talk in HALL 2 at 11:15</title>
        <persons>
          <person id='1'>Alice</person>
          <person id='4'>Dick</person>
        </persons>
      </event>
    </room>
  </day>
</schedule>
```

From this file **VOC2MIX** will generate the following file names (and descriptions) for which it will search:

```txt
event_1_persons.png|How voctocore improved our lifestyle - Alice, Bob, Claire
event_1_person_1.png|Alice
event_1_person_2.png|Bob
event_1_person_3.png|Claire

event_2_persons.png|How having a winkekatze changed me - Dick
event_2_person_4.png|Dick

event_3_persons.png|You won't believe what happened next! - Alice, Dick
event_3_person_1.png|Alice
event_3_person_4.png|Dick
```

**VOC2CORE** will present a list of all available (files present in file system) overlays if asked for.

###### 1.6.1.4.3.1. Filtering Events

If you have multiple events in multiple rooms it might be of need to filter the current event which you are mixing.
The first filter criteria will always be the current time.
**VOC2MIX** automatically filters out events that are past or in future.

Additionally you might set the room ID to filter out all events which are not happening in the room you are mixing.

```ini
[overlay]
schedule=schedule.xml
room=HALL 1
```

Now **VOC2CORE** will list you the available overlay images only for room `HALL 1`.

##### 1.6.1.4.4. Additional Overlay Options

###### 1.6.1.4.4.1. Auto-Off

**VOC2GUI** presents a button called `auto-off` which can be switched on and off.
Selection a different insertion from the list or the change of the current composite will force to end a current insertion.
This is used to prevent uncomfortable visual effects.

```ini
[overlay]
user-auto-off = true
auto-off = false
blend-time=300
```

If `user-auto-off` is set the button can be switched by the user and it is present within the user interface of **VOC2GUI**.
`auto-off` sets the initial state of the auto-off feature.
And `blend-time` sets the duration of the in and out blending of overlays in milliseconds.

### 1.6.2. Output Elements

#### 1.6.2.1. Mix Live

This is the mix that is intended as output for live streaming. It get blanked by the stream blanker when
the live button in the GUI is disabled.

#### 1.6.2.2. Mix Recording

This is the mix that is intended as output for recording. It is identical to the video displayed int the GUI as **MIX**.

#### 1.6.2.3. Mix Preview

This mix is intended for the **MIX** preview in the GUI.

#### 1.6.2.4. Sources Live

#### 1.6.2.5. Sources Recording

`local_recording` is not yet implemented for 2.0

#### 1.6.2.6. Sources Preview

Source Preview elements are used to encode the different video streams which will be shown in the GUI.
If previews are not enabled the GUI will use the raw video mirror ports. This only can work if gui and core are running on the same machine.

```ini
[previews]
enabled = true
live = true
vaapi=h264
videocaps=video/x-raw,width=1024,height=576,framerate=25/1
```

| Attribute Name     | Example Values                      | Default     | Description
| ------------------ | ----------------------------------- | ----------- | -----------------------------------------
| `enable`           | `true`                              | false       | video4linux2 device to use
| `live`            | `true`                               | false       | video width expected from the source
| `vaapi`           | `h264`                               |             | h264, mpeg2 and jpeg are supported. If jpeg is used CPU decoding needs to be used ob the gui.
| `scale-method`    | 2                                    | 0           | 0: Default scaling mode 1: Fast scaling mode, at the expense of quality 2: High quality scaling mode, at the expense of speed.
| `vaapi-denoise`   | true                                 | false       | use VAAPI to denoise the video before encoding it

#### 1.6.2.7. Mirror Ports

Mirror ports provide a copy of the input stream of each source via an TCP port.

```ini
[mirrors]
enabled=true
```

| Attribute Name     | Example Values                      | Default     | Description
| ------------------ | ----------------------------------- | ----------- | -----------------------------------------
| `enable`           | `true`                              | false       |

#### 1.6.2.8. SRT Server

`srtserver` not yet implemented for 2.0

#### 1.6.2.9. Program Output

Outputs the current **Mix Recording** (aka **Mix** in GUI) to a defined gstreamer sink

```ini
[programoutput]
enabled = true
videosink = autovideosink # this is the default
audiosink = autoaudiosink # this is the default
```

##### 1.6.2.9.1. AJA Program Output

You can, for instance, output the Mix recording to an AJA card (including one
from which you are capturing):

```ini
[programoutput]
enabled = true
# channel=4 --> SDI 5
videosink=queue max-size-bytes=0 max-size-buffers=0 max-size-time=1000000000 ! videoconvert ! video/x-raw,width=1920,height=1080,framerate=60/1 ! ajaout.video ajasinkcombiner name=ajaout ! ajasink channel=4 reference-source=input-1
# Note that the audio buffers must be padded to 16 channels and chunked at the framerate or the pipeline will stall or sound very odd
audiosink=audiomixmatrix in-channels=2 out-channels=16 channel-mask=-1 mode=first-channels ! audiobuffersplit output-buffer-duration=1/60 ! ajaout.audio
```

### 1.6.3. A/V Processing Elements

#### 1.6.3.1. DeMux

#### 1.6.3.2. Mux

### 1.6.4. Video Processing Elements

#### 1.6.4.1. Scale

#### 1.6.4.2. Mix Compositor

#### 1.6.4.3. Mix Blinding Compositor

#### 1.6.4.4. Sources Blinding Compositor

### 1.6.5. Audio Processing Elements

#### 1.6.5.1. Audio Mixer

#### 1.6.5.2. Audio Blinding Mixer

### 1.6.6. Live Sources

If you want to expose sources (e.g. a slide grabber) as an additional output for recording and streaming purposes, use the `mix/livesources` directive, which takes a comma-separated list of sources to be exposed, like so:

```ini
[mix]
sources=cam1,cam2,grabber
livesources=grabber
```

This will expose the grabber on port 15001. If you specify further sources, they will appear on ports 15002, etc.

## 1.7. Decoder and Encoder

Voc2mix needs to encoder and decode video on different place in the pipeline as well as in the GUI.
Encoding and decoding can consume much time of the CPU. Therefore this tasks can be offloaded to fixed function en-/decoder blocks.
Probably the most common architecture for this, at least on x86, is Intels VAAPI interface which is is not limited to intel GPUs.
Most Intel CPUs with build in GPU provide these functions with different feature sets.
As there is also a penalty one using these as the data needs to be up and downloaded to the GPU the impact of using a offloading in favor of
CPU en-/decoding differs depending an a number of variables.
Also the quality that can be expected from offloading differs on the hardware used.

### 1.7.1. CPU

Voc2mix can use all software en-/decoder gstreamer provides. The current code offer h264, mpeg2 and jpeg.

### 1.7.2. VAAPI

* <https://www.freedesktop.org/wiki/Software/vaapi/>
* <https://01.org/linuxmedia/vaapi>
* <https://en.wikipedia.org/wiki/Video_Acceleration_API>

To use VAAPI with voc2mix on intel GPUs at least a sandy bridge generation CPU is required.
Voc2mix can use the the vaapi encoder to encode the preview stream for the GUI.
The GUI it self can use VAAPI to decode the preview streams and also use VAAPI as video system do draw the video to the screen.
Both can significant reduce the CPU load.

En-/decoding with an NVIDIA GeForce 940MX also seems to work but there are issues when vaapi is also used as video system.
