# Server-Pipeline Structure
````
16000 BackgroundSource
                      \
                       --> VideoMix
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

< set_stream_blank pause
> ok

< set_stream_live
> ok

…

> signal set_video_a cam1
> signal set_composite_mode side_by_side_equal

````

# Messages
Messages are Client-to-Client information that don't touch the server, while being distributed on its control-socket:
````
< message foo bar moo
> ok

… on a nother connection

> signal message foo bar moo
````
