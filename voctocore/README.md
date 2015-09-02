# Voctocore - The videomixer core-process

## Design goals
Our Design is heavily influenced by gst-switch. We wanted a small videomixer core-process, whose sourcecode can be read and understand in about a weekend.
All Sources (Cameras, Slide-Grabbers) and Sinks (Streaming, Recording) should be separate Processes. As far as possible we wanted to reuse our existing and well-tested ffmpeg Commandlines for streaming and recording. It should be possible to connect additional Sinks at any time while the number of Sources is predefined in our Setup. All sources and sinks should be able to die and get restarted without taking the core process down.
While Sources ans Sinks all run on the same Machine, Control- or Monitoring-Clients, for example a GUI, should be able to run on a different machine and connect to the core-process via Gigabit Ethernet. The core-process should be controllable by a very simple protocol which can easily be scripted or spoken with usual networking tools.

## Design decisions
To meet our goal of "read and understand in about a weekend" python was chosen as language for the high-level parts, with [GStreamer](http://gstreamer.freedesktop.org/) for the low-level media handling. GStreamer can be controlled via the [PyGI](https://wiki.gnome.org/action/show/Projects/PyGObject) bindings from Python.
As an Idea borrowed from gst-switch, all Video- and Audio-Streams to and from the core are handled via TCP-Connections. Because they transport raw Video-Frames the only reasonable transport is via the loopback interface or a dedicated GBit-NIC (1920×1080×2 (I420)×8 (Bits)×25 (fps) = ~830 MBit/s). Nevertheless TCP is a quite efficient and good supported transport mechanism. For compatibility with ffmpeg and because of its good properties when streamed over TCP, [Matroska](http://www.matroska.org/) was chosen as a Container.

The ubiquitous Input/Output-Format into the core-process is therefore Raw I420 Frames and Raw S16LE Audio in a Matroska container for Timestamping via TCP over localhost. Network handling is done in python, because it allows for greater flexibility. After the TCP connection is ready, its file descriptor is passed to GStreamer which handles the low-level read/write operations. To be able to attach/detach sinks, the `multifdsink`-Element can be used. For the Sources it's more complicated:

When a source is not connected, its video and audio stream must be substituted with black frames ans silence, to that the remaining parts of the pipeline can keep on running. To achive this, a separate GStreamer-Pipeline is launched for an incoming Source-Connection and destroyed in case of a disconnect or an error. To pass Video -and Audio-Buffers between the Source-Pipelines and the other parts of the Mixer, we make use of the `inter(audio/video)(sink/source)`-Elements. `intervideosrc` and `interaudiosrc` implement the creation of black frames and silence, in case no source is connected or the source broke down somehow.

If enabled in Config, the core process offers two formats for most outputs: Raw-Frames in mkv as described above, which should be used to feed recording or streaming processes running on the same machine. For the GUI which usually runs on a different computer, they are not suited because of the bandwidth requirements (1920×1080 I420 @25fps = 791 MBit/s). For this reason the Servers offers Preview-Ports for each Input and the Main-Mix, which serves the same content, but the video frames there are jpeg compressed, combined with uncompressed S16LE audio and encapsulated in mkv.

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

*)  only when [previews] enabled=true is configured
**) only when [stream-blanker] enabled=true is configured
````

## Network Ports Listing
Ports that will accept Raw I420 Frames and Raw S16LE Audio in a Matroska container:
 - 10000, 10001, … – Main Video-Sources, depending on the number of configured Sources

Ports that will accept Raw I420 Frames without Audio in a Matroska container:
 - 16000 Mixer – Background Loop
 - 17000, 17001, … – Stream-Blanker Video-Input, depending on the number of configured Stream-Blanker-Sources

Ports that will accept Raw S16LE Audio wihout Video in a Matroska container:
 - 18000 – Stream-Blanker Audio-Input

Ports that will provide Raw I420 Frames and Raw S16LE Audio in a Matroska container:
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
The Client may send Commands listed in the [Commands-File](./voctocore/lib/commands.py). Each Command takes a number of Arguments which are separated by Space. There is currently no way to escape Spaces or Linebreaks in Arguments. A Command ends with a Unix-Linebreak. A Client may not send multiple Commands on the same Socket without waiting for the response but it is possible to send multiple Commands to multiple Connections to the Control-Server in Parallel.

### 2. Server Responses to Commands
The Server either responds with `ok` followed by one ore more Arguments, or with `error` followed by a Human Readable error message. A Machine-Readable error code is currently not available. The Response always ends with a Unix Linebreak.

There are two Kinds of Commands: `set` and `get`. `set`-Commands change the Mixer state and are only acknowledged with a single `ok`. `get`-Commands retrieve Information about the Mixers state and respond with an `ok` followed by Arguments.

### 3. Server Signals
When another Client issues a Command and the Server executed it successfully, the Server will signal this with a Line starting with `signal` followed by the Command and all Parameters received. Only `set`-Commands trigger a `signal`.

### Example Communication:
````
< set video a cam1
> ok cam1

< set composite side_by_side_equal
> ok side_by_side_equal

< get output port
> ok 11000

< get video a
> ok cam1

< get composite
> ok side_by_side_equal

< set video a blafoo
> error "blafoo" is no known src

< set status blank pause
> ok blank pause

< set status live
> ok live

…

> signal set video a cam1
> signal set composite side_by_side_equal

````

### Messages
Messages are Client-to-Client information that don't change the Mixers state, while being distributed throuh its Control-Socket.

````
< message cut bar moo
> ok

… on a nother connection

> signal message foo bar moo
````

They can be used to Implement Features like a "Cut-Button" in the GUI. When Clicked the GUI would emit a message to the Server which would distribute it to all Control-Clients. A recording Script may receive the notification and rotate its output-File.

## Configuration
On Startup the Video-Mixer reads the following Configuration-Files:
 - <install-dir>/default-config.ini
 - <install-dir>/config.ini
 - /etc/voctomix.ini
 - <homedir>/.voctomix.ini
 - <File specified on Command-Line via --ini-file>

From top to bottom the individual Settings override previous Settings. `default-config.ini` should not be edited, because a missing Setting will result in an Exception.

All Settings configured in the Server are available via the `get_setting` Call on the Control-Port and will be used by the Clients, so there will be no need to duplicate Configuration options between Server and Clients.
