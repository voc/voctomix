./gst-launch-1.0.exe videotestsrc pattern=black !  `
videoconvert ! `
videorate ! `
video/x-raw,format=I420,width=1920,height=1080,framerate=30/1,pixel-aspect-ratio=1/1! `
mux. `
directsoundsrc name=directsound1 ! `
audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000! `
mux. `
matroskamux name=mux ! `
tcpclientsink host=172.30.9.163 port=10000