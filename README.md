# Voctomix
The [C3Voc](https://c3voc.de/) creates Lecture Recordings from German Hacker/Nerd Conferences. We have used [dvswitch](http://dvswitch.alioth.debian.org/wiki/) very successfully in the past but it has some serious limitations, which in 2014 we started looking for a replacement. We tested [snowmix](http://sourceforge.net/projects/snowmix/) and [gst-switch](https://github.com/timvideos/gst-switch) and while both did some things we wanted right, we realised that no existing tool would be able to fulfil all our whishes. Furthermore both are a nightmare to extend. So we decided to build our own Implementation of a Live-Video-Mixer.

## Subprojects
The Voctomix Project consists of three parts:
 - [Voctocore](./voctocore/), the videomixer core-process that does the actual video- and audio crunching
 - [Voctogui](./voctogui/), a GUI implementation in GTK controlling the core's functionality and giving visual feedback of the mixed video
 - Voctotools (tbd.), a Collection of Tools and Examples on how to talk to the core-process, feeding and receiving video-streams

## Patch policy
The main Goal of Voxtomix is to build a Videomixer that suites the C3Vocs requirements, which means it may not directly suite your Requirements. Following the 'code over configuration' pattern we are not planning to make voctomix a general purpose video editing tool, so we may not accept feature-requests which contradict the C3Voc's requirements or introduce extra complexity without adding much value to the C3Voc's processes.
Instead, you need something really speacial, you are encouraged to fork Voctomix and modify it to your needs. The code should be simple enough to do this and we will help you with that, if required.

## Contact
To get in touch with us we'd ask to join `#voc-lounge` on the hackint IRC network, mail to `voc AT c3voc DOT de` or meet us on one of the [many conferences](https://c3voc.de/eventkalender) we're at.
You may also want to watch [a Presentation](https://media.ccc.de/v/froscon2015-1520-conference_recording_und_streaming#video) some of us gave about our Video-Infrastructure.
