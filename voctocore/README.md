# Server-Pipeline Structure
````
                       /-> VideoMix
                      /             \
                     /               \    /-> StreamBlanker -> StreamOutputPort 15000
                    /                 ------> OutputPort 11000
                   /                 /    \-> Encoder* -> PreviewPort* 12000
                  /                 /
                 /----- -> AudioMix
                /
10000… AVSource --> MirrorPort 13000…
                \-> Encoder* -> PreviewPort* 14000…

*) only when encode_previews=true is configured
````

# Control Protocol
TCP-Port 9999
````
< set_video_a cam1
> ok

< set_composite_mode side_by_side_equal
> ok

< get_output_port
> ok 11000

< get_video_a
> ok 0 cam1

< set_composite_mode
> ok side_by_side_equal

< set_video_a blafoo
> error "blafoo" is no known src

…

> signal set_video_a cam1
> signal set_composite_mode side_by_side_equal

````
