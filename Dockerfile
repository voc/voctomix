## initial build:
# docker build -t local/voctomix .
## re-build:
# docker tag local/voctomix:latest local/voctomix:old; docker build -t local/voctomix . && docker rmi local/voctomix:old
#
## run:
# docker run -it --rm local/voctocore help
#
## core:
# docker run -it --rm -v /some/dir:/video
#   -p 9999:9999 -p 10000:10000 -p 10001:10001 -p 10002:10002 -p 11000:11000 -p 12000:12000 \
#   -p 13000:13000 -p 13001:13001 -p 13002:13002 -p 13100:13100 -p 14000:14000 -p 15000:15000 -p 16000:16000 \
#   -p 17000:17000 -p 17001:17001 -p 17002:17002 -p 18000:18000 --name=voctocore local/voctomix core
#
## test sources 
# docker run -it --rm --name=cam1 --link=voctocore:corehost local/voctomix gstreamer/source-videotestsrc-as-cam1.sh
# docker run -it --rm --name=bg --link=voctocore:corehost local/voctomix gstreamer/source-videotestsrc-as-background-loop.sh#
#
## gui
## gui will connect to "corehost": corehost is aliased to container "voctocore"
# xhost +local:$(id -un)
# docker run -it --rm --name=gui --env=gid=$(id -g) --env=uid=$(id -u) --env=DISPLAY=:0 --link=voctocore:corehost \
#  -v /tmp/vocto/configgui.ini:/opt/voctomix/voctogui/config.ini -v /tmp/.X11-unix:/tmp/.X11-unix -v /tmp/.docker.xauth:/tmp/.docker.xauth local/voctomix gui


FROM ubuntu:wily

MAINTAINER Bjoern Riemer <bjoern.riemer@web.de>

ENV DEBIAN_FRONTEND noninteractive

ENV uid 1000
ENV gid 1000

RUN useradd -m voc

RUN apt-get update \
    && apt-get install -y \
        gstreamer1.0-plugins-good \
        wget \
    && apt-get install -y --no-install-recommends \
        gstreamer1.0-tools \
        libgstreamer1.0-0 \
        python3 \
        python3-gi \
        gir1.2-gstreamer-1.0 \
        gstreamer1.0-plugins-bad \
    && apt-get install -y \
        gir1.2-gst-plugins-base-1.0 \
        gir1.2-gstreamer-1.0 \
        gir1.2-gtk-3.0 \
        gstreamer1.0-x \
        ffmpeg \
        python3-gi-cairo \
    && apt-get clean

RUN wget -q https://github.com/tianon/gosu/releases/download/1.7/gosu-amd64 -O /bin/gosu && chmod +x /bin/gosu

RUN mkdir -p /opt/voctomix

EXPOSE 9998 9999 10000 10001 10002 11000 12000 13000 13001 13002 13100 14000 15000 16000 17000 17001 17002 18000 
VOLUME /video

WORKDIR /opt/voctomix
COPY . /opt/voctomix/
COPY docker-ep.sh /opt/voctomix/

RUN sed -i 's/localhost/corehost/g' voctogui/default-config.ini ;\
    sed -i 's/system=gl/system=xv/g' voctogui/default-config.ini ;\
    find /opt/voctomix/example-scripts/ -type f -exec sed -i 's/localhost/corehost/g' {} \;

ENTRYPOINT ["/opt/voctomix/docker-ep.sh"]
CMD ["help"]
