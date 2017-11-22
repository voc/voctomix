# Voctocore - The videomixer core-process

## Design goals
Our Design is heavily influenced by gst-switch. We wanted a small videomixer core-process, whose sourcecode can be read and understand in about a weekend.
All Sources (Cameras, Slide-Grabbers) and Sinks (Streaming, Recording) should be separate Processes. As far as possible we wanted to reuse our existing and well-tested ffmpeg Commandlines for streaming and recording. It should be possible to connect additional Sinks at any time while the number of Sources is predefined in our Setup. All sources and sinks should be able to die and get restarted without taking the core process down.
While Sources and Sinks all run on the same Machine, Control- or Monitoring-Clients, for example a GUI, should be able to run on a different machine and connect to the core-process via Gigabit Ethernet. The core-process should be controllable by a very simple protocol which can easily be scripted or spoken with usual networking tools.

## Design decisions
To meet our goal of "read and understand in about a weekend" python was chosen as language for the high-level parts, with [GStreamer](http://gstreamer.freedesktop.org/) for the low-level media handling. GStreamer can be controlled via the [PyGI](https://wiki.gnome.org/action/show/Projects/PyGObject) bindings from Python.
As an Idea borrowed from gst-switch, all Video- and Audio-Streams to and from the core are handled via TCP-Connections. Because they transport raw Video-Frames the only reasonable transport is via the loopback interface or a dedicated GBit-NIC (1920×1080×2 (UYVY)×8 (Bits)×25 (fps) = ~830 MBit/s). Nevertheless TCP is a quite efficient and good supported transport mechanism. For compatibility with ffmpeg and because of its good properties when streamed over TCP, [Matroska](http://www.matroska.org/) was chosen as a Container.

The ubiquitous Input/Output-Format into the core-process is therefore Raw UYVY Frames and Raw S16LE Audio in a Matroska container for Timestamping via TCP over localhost. Network handling is done in python, because it allows for greater flexibility. After the TCP connection is ready, its file descriptor is passed to GStreamer which handles the low-level read/write operations. To be able to attach/detach sinks, the `multifdsink`-Element can be used. For the Sources it's more complicated:

When a source is not connected, its video and audio stream must be substituted with black frames and silence, to that the remaining parts of the pipeline can keep on running. To achive this, a separate GStreamer-Pipeline is launched for an incoming Source-Connection and destroyed in case of a disconnect or an error. To pass Video -and Audio-Buffers between the Source-Pipelines and the other parts of the Mixer, we make use of the `inter(audio/video)(sink/source)`-Elements. `intervideosrc` and `interaudiosrc` implement the creation of black frames and silence, in case no source is connected or the source broke down somehow.

If enabled in Config, the core process offers two formats for most outputs: Raw-Frames in mkv as described above, which should be used to feed recording or streaming processes running on the same machine. For the GUI which usually runs on a different computer, they are not suited because of the bandwidth requirements (1920×1080 UYVY @25fps = 791 MBit/s). For this reason the Servers offers Preview-Ports for each Input and the Main-Mix, which serves the same content, but the video frames there are jpeg compressed, combined with uncompressed S16LE audio and encapsulated in mkv.

Also, if enabled in Config, another Building-Block is chained after the Main-Mix: the StreamBlanker. It is used in Cases when there should be no Stream, for example in Breaks between Talks. It is sourced from one ASource which usually accepts a Stream of Music-Loop and one or more VSources which usually accepts a "There is currently no Talk"-Loop. Because multiple VSources can be configured, one can additionally source a "We are not allowed to Stream this Talk" or any other Loop. All Video-Loops are combined with the Audio-Loop and can be selected from the GUI.

## Block-Level Diagram
````
17000… VSource** (Stream-Blanker) ---\
18000  ASource** (Stream-Blanker) ----\
                                       \
16000 VSource (Background)              \
                      \                  \
                       --> VideoMix       \
                      /             \      -> StreamBlanker** -> StreamOutputPort** 15000
                     /               \    /
                    /                 ------> OutputPort 11000
                   /                 /    \-> Encoder* -> PreviewPort* 12000
                  /                 /
                 /----- -> AudioMix
                /
10000… AVSource --> MirrorPort 13000…
                \-> Encoder* -> PreviewPort* 14000…

9999 Control-Server
9998 GstNetTimeProvider Network-Clock

*)  only when [previews] enabled=true is configured
**) only when [stream-blanker] enabled=true is configured
````

## Network Ports Listing
Ports that will accept Raw UYVY Frames and Raw S16LE Audio in a Matroska container:
 - 10000, 10001, … – Main Video-Sources, depending on the number of configured Sources

Ports that will accept Raw UYVY Frames without Audio in a Matroska container:
 - 16000 Mixer – Background Loop
 - 17000, 17001, … – Stream-Blanker Video-Input, depending on the number of configured Stream-Blanker-Sources

Ports that will accept Raw S16LE Audio wihout Video in a Matroska container:
 - 18000 – Stream-Blanker Audio-Input

Ports that will provide Raw UYVY Frames and Raw S16LE Audio in a Matroska container:
 - 13000, 13001, … – Main Video-Source Mirrors, depending on the number of configured Sources
 - 11000 – Main Mixer Output
 - 15000 – Stream Output – only when [stream-blanker] enabled=true is configured

Ports that will provide JPEG Frames and Raw S16LE Audio in a Matroska container – only when [previews] enabled=true is configured
 - 14000, 14001, … – Main Video-Source Mirrors, depending on the number of configured Sources
 - 12000 – Main Mixer Output

Port 9999 will Accept Control Protocol Connections.

## Control Protocol
To Control operation of the Video-Mixer, a simple line-based TCP-Protocol is used. The Video-Mixer accepts connection on TCP-Port 9999. The Control-Protocol is currently unstable and may change in any way at any given time. Regarding available Commands and their Reponses, the Code is the Documentation. There are 3 kinds of Messages:

### 1. Commands from Client to Server
The Client may send Commands listed in the [Commands-File](./lib/commands.py). Each Command takes a number of Arguments which are separated by Space. There is currently no way to escape Spaces or Linebreaks in Arguments. A Command ends with a Unix-Linebreak.

There are two Kinds of Commands: `set_*` and `get_*`. `set`-Commands change the Mixer state while `get`-Commands dont. Both kinds of Commands are answered with the same Response-Message.

For example a `set_video_a cam1` Command could be respnded to with a `video_status cam1 cam2` Response-Message. A `get_video` Command will be answered with exactly the same Message.

### 2. Errors in response to Commands
When a Command was invalid or had invalid Parameters, the Server responds with `error` followed by a Human Readable error message. A Machine-Readable error code is currently not available. The Error-Response always ends with a Unix Linebreak (The Message can not contain Linebreaks itself).

### 3. Server Signals
When another Client issues a Command and the Server executed it successfully, the Server will signal this to all connected Clients. The Signal-Message format is identical to the Response-Format of the issued Command.

For example if Client `A` issued Command `set_video_a cam1`, Client `A`and Client `B` will both receive the same `video_status cam1 cam2` Response-Message.

### Example Communication:
````
< set_video_a cam1
> video_status cam1 cam2

< set_composite_mode side_by_side_equal
> composite_mode side_by_side_equal

< set_videos_and_composite grabber * fullscreen
> video_status grabber cam1
> composite_mode fullscreen

< get_video
> video_status cam2 cam1

< get_composite_mode
> composite_mode fullscreen

< set_video_a blafoo
> error unknown name foo

< get_stream_status
> stream_status live

< set_stream_blank pause
> stream_status blank pause

< set_stream_live
> stream_status live

… meanwhile in another control-server connection

> video_status cam1 cam2
> video_status cam2 cam1
> composite_mode side_by_side_equal
> composite_mode fullscreen
> stream_status blank pause
> stream_status live

````

### Messages
Messages are Client-to-Client information that don't change the Mixers state, while being distributed throuh its Control-Socket.

````
< message cut bar moo
> message cut bar moo

… meanwhile in another control-server connection

> message cut bar moo
````

They can be used to Implement Features like a "Cut-Button" in the GUI. When Clicked the GUI would emit a message to the Server which would distribute it to all Control-Clients. A recording Script may receive the notification and rotate its output-File.

## Configuration
On Startup the Video-Mixer reads the following Configuration-Files:
 - `<install-dir>/default-config.ini`
 - `<install-dir>/config.ini`
 - `/etc/voctomix/voctocore.ini`
 - `/etc/voctocore.ini`
 - `<homedir>/.voctocore.ini`
 - `<File specified on Command-Line via --ini-file>`

From top to bottom the individual Settings override previous Settings. `default-config.ini` should not be edited, because a missing Setting will result in an Exception.

All Settings configured in the Server are available via the `get_config` Call on the Control-Port and will be used by the Clients, so there will be no need to duplicate Configuration options between Server and Clients.

## Multi-Stream Audio Mixing
Voctomix has support for passing and mixing as many audio streams as desired. At the c3voc we use this feature for recording lectures with simultaneous translation. The number of streams is configured system-wide with the `[mix] audiostreams` setting which defaults to 1. All streams are always stereo. Setting it to 3 configures 3 stereo-streams.

Each tcp-feed for a camera (not stream-blanker and background-feeds) then needs to follow this channel layout (in this example: have 3 stereo-stream) or it will stall after the first couple seconds.

Similar all output-streams (mirrors, main-out, stream-out) will now present 3 stereo-streams. The streamblanker will correctly copy the blank-music to all streams when the stream-blanker is engaged.

For the internal decklink-sources, you have to configure the mapping in the source-section of the config:
```
[mix]
…
audiostreams = 3

[source.cam1]
kind = decklink
devicenumber = 0
video_connection = SDI
video_mode = 1080p25
audio_connection = embedded

# Use audio from this camera
volume=1.0

# Map SDI-Channel 0 to the left ear and Channel 1 to the right ear of the Output-Stream 0
audiostream[0] = 0+1

[source.cam2]
kind = decklink
devicenumber = 1
video_connection = SDI
video_mode = 1080p25
audio_connection = embedded

# Use audio from this camera
volume=1.0

# Map SDI-Channel 0 to both ears ear of the Output-Stream 1
audiostream[1] = 0

# Map SDI-Channel 1 to both ears ear of the Output-Stream 2
audiostream[2] = 1
```

With Audio-Embedders which can embed more then 2 Channels onto an SDI-Stream you can also fill all Streams from one SDI-Source. This requires at least GStreamer 1.12.3:
```
[mix]
…
audiostreams = 3

[source.cam1]
kind = decklink
devicenumber = 0
video_connection = SDI
video_mode = 1080p25
audio_connection = embedded

# Use audio from this camera
volume=1.0

# Map SDI-Channel 0 to the left ear and Channel 1 to the right ear of the Output-Stream 0
audiostream[0] = 0+1
audiostream[1] = 2+3
audiostream[2] = 4+5
```
