# Voctomix
The [C3Voc](https://c3voc.de/) creates Lecture Recordings from German Hacker/Nerd Conferences. We have used [dvswitch](http://dvswitch.alioth.debian.org/wiki/) very successfully in the past but it has some serious limitations, which in 2014 we started looking for a replacement. We tested [snowmix](http://sourceforge.net/projects/snowmix/) and [gst-switch](https://github.com/timvideos/gst-switch) and while both did some things we wanted right, we realised that no existing tool would be able to fulfil all our whishes. Furthermore both are a nightmare to extend. So we decided to build our own Implementation of a Live-Video-Mixer.

## Subprojects
The Voctomix Project consists of three parts:
 - [Voctocore](./voctocore/), the videomixer core-process that does the actual video- and audio crunching
 - [Voctogui](./voctogui/), a GUI implementation in GTK controlling the core's functionality and giving visual feedback of the mixed video
 - Voctotools (tbd.), a Collection of Tools and Examples on how to talk to the core-process, feeding and receiving video-streams

## Contact
To get in touch with us we'd ask to join `#voc-lounge` on the hackint IRC network, mail to `voc AT c3voc DOT de` or meet us on one of the [many conferences](https://c3voc.de/eventkalender) we're at.
You may also want to watch [a Presentation](https://media.ccc.de/v/froscon2015-1520-conference_recording_und_streaming#video) some of us gave about our Video-Infrastructure.
