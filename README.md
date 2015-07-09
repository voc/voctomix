# Voctomix
The [C3Voc](https://c3voc.de/) creates Lecture Recordings from German Hacker/Nerd Conferences. We have used [dvswitch](http://dvswitch.alioth.debian.org/wiki/) very successfully in the past but it has some serious limitations, which in 2014 we started looking for a replacement. We tested [snowmix](http://sourceforge.net/projects/snowmix/) and [gst-switch](https://github.com/timvideos/gst-switch) and while both did some things we wanted right, we realised that no existing tool would be able to fulfil all our whishes. Furthermore both are a nightmare to extend. So we decided to build our own Implementation of a Live-Video-Mixer.

## Subprojects
The Voctomix Project consists of three parts:
 - [VoctoVore](./voctocore/), the videomixer core-process that does the actual video- and audio crunching
 - [Voctogui](./voctogui/), a GUI implementation in GTK controlling the core's functionality and giving visual feedback of the mixed video
 - Voctotools (tbd.), a Collection of Tools and Examples on how to talk to the core-process, feeding and reciving video-streams

## Patch policy
The main Goal of Voxtomix is to build a Videomixer that suites the C3Vocs requirements, which means it will not directly suite your Requirements. We are not planning to make it an all-purpose Tool. Instead, you are encouraged to fork Voctomix and modify it to your needs. The code should be simple enough to do this and we will help you deciding with that, if required. Because of this we probably won't accept Feature-Patches which add features the C3Voc doesn't need.

## Contact
To get in touch with us we'd ask to join #voc on the hackint IRC network.
