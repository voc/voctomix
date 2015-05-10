# Server-Pipeline Structure
````
                              /-> Encoder -> PreviewPort 12000
                 /-> VideoMix --> OutputPort 11000
                /             \-> StreamBlanker -> StreamOutputPort 11001
10000… VideoSrc --> MirrorPort 13000…
                \-> Encoder -> PreviewPort 14000…

                              /-> Encoder -> PreviewPort 22000
                 /-> AudioMix --> OutputPort 21000
                /             \-> StreamBlanker -> StreamOutputPort 21001
20000… AudioSrc --> MirrorPort 23000…
                \-> Encoder -> PreviewPort 24000…
````

# Control Protocol
TCP-Port 9999
````
< set_video_a cam1
> ok

< set_composite_mode side_by_side_equal
> ok

< get_video_output_port
> ok 11000

< get_video_a
> ok 0 cam1

< set_composite_mode
> ok side_by_side_equal

< set_video_a blafoo
> error "blafoo" is no known src
````
