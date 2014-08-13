# Voctomix
Building a HD-Compatible, Multi-Track-Audio-Capable Software-Based Live-Video-Mixer for the VOC/FEM.

# Build Requirements GSteamer 1.4 Debian Stable
sudo apt-get install build-essential libglib2.0-dev gobject-introspection gtk-doc-tools flex bison automake autopoint libtool libx11-dev libasound2-dev libsoup2.4-dev libpng12-dev libjpeg8-dev libcairo2-dev libx264-dev libmpeg2-4-dev libmp3lame-dev libtwolame-dev libmad0-dev libcurl4-openssl-dev libfaad-dev nettle-dev libneon27-dev librsvg2-dev librtmp-dev yasm nasm
sudo apt-get -t wheezy-backports install liborc-0.4-dev libopus-dev

fix `version=2.40` in /usr/lib/x86_64-linux-gnu/pkgconfig/libsoup-2.4.pc

gst-plugins-bad $ ./autogen.sh ­-- --disable-gl
