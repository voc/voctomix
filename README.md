# Voctomix
The [C3Voc](https://c3voc.de/) creates Lecture Recordings from German Hacker/Nerd Conferences. We have used [dvswitch](http://dvswitch.alioth.debian.org/wiki/) very successfully in the past but it has some serious limitations, which in 2014 we started looking for a replacement. We tested [snowmix](http://sourceforge.net/projects/snowmix/) and [gst-switch](https://github.com/timvideos/gst-switch) and while both did some things we wanted right, we realised that no existing tool would be able to fulfil all our whishes. Furthermore both are a nightmare to extend. So we decided to build our own Implementation of a Live-Video-Mixer.

## Subprojects
The Voctomix Project consists of three parts:
 - [Voctocore](./voctocore/), the videomixer core-process that does the actual video- and audio crunching
 - [Voctogui](./voctogui/), a GUI implementation in GTK controlling the core's functionality and giving visual feedback of the mixed video
 - Voctotools (tbd.), a Collection of Tools and Examples on how to talk to the core-process, feeding and receiving video-streams

## Installation
Voctomix requires a fairly recent Version of GStreamer (at least 1.5, though we recommend 1.6 and later). Because we are using Debian Jessie as our production system, we are packaging the required Libraries in our own Debian Repository. The Packages inside this Repository are built against deb-multimedia.org, so to use them you should add the following lines to your `/etc/apt/sources.list`:
````
deb http://www.deb-multimedia.org jessie main non-free
deb http://c3voc.de/voctomix jessie non-free
````

You'll then need install the GPG-Keys:
````
apt-get update
apt-get install deb-multimedia-keyring
curl https://c3voc.de/voctomix/gpg-key.asc | apt-key add -
apt-get update
````

Before you can install the required Dependencies:
````
apt-get install gstreamer1.0-libav gstreamer1.0-plugins-bad gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly gstreamer1.0-tools libgstreamer1.0-0 python3 python3-gi gir1.2-gstreamer-1.0
````

For the GUI you'll -- additionally to a gnome-desktop -- need to install the following dependencies:
````
apt-get install gstreamer1.0-alsa
````

Now you should be able to clone the Git-Repository and run Voctomix or the GUI like this:
````
git clone https://github.com/voc/voctomix.git
cd voctomix
./voctocore/voctocore.py
./voctocore/voctogui.py
````

## A word on CPU-Usage
Voctomix requires a fair amount of CPU-Time to run in the default configuration of 1920×1080 at 25fps. Our Production-Systems have these CPUs: `Intel Core i7-3770 CPU 4x 3.40GHz` but we're also experimenting with newer ones like these: `Intel Core i7-6700K, 4x 4.00GHz`.
For testing and development you may want to use a `config.ini` that reduces the resolution and also turns off the JPEG-Preview-Encoders, which take a huge amount of the required CPU-Power and are not required, as long as the GUI and the Core run on the same machine (or have a 10GE Link between them, FWIW).

Such a config.ini might look like this:
````
[mix]
videocaps=video/x-raw,format=I420,width=320,height=180,framerate=25/1,pixel-aspect-ratio=1/1

[previews]
enabled=false
videocaps=video/x-raw,width=320,height=180,framerate=25/1
````

## A word on running in a VM
While the Core runs fine inside a VM (like [VirtualBox](https://www.virtualbox.org/)), the GUI usually uses the [X11-Xv-Extension](https://en.wikipedia.org/wiki/X_video_extension) to play back video into the X11-Server. This Extension is not supported on most VMs, so to run inside such a VM you'll need to tell the GUI to fall back to using traditional X-Images by using a `config.ini` on the GUI with this option:
````
[x11]
xv=false
````

## Contact
To get in touch with us we'd ask to join `#voc-lounge` on the hackint IRC network, mail to `voc AT c3voc DOT de` or meet us on one of the [many conferences](https://c3voc.de/eventkalender) we're at.
You may also want to watch [a Presentation](https://media.ccc.de/v/froscon2015-1520-conference_recording_und_streaming#video) some of us gave about our Video-Infrastructure.
