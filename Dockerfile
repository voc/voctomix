## re-build:
# docker tag local/voctomix:latest local/voctomix:old; docker build -t local/voctomix . && docker rmi local/voctomix:old
## build:
# docker build -t bjoernr/voctomix .
## run:
# docker run -it --rm bjoernr/voctocore help
## core:
# docker run -it --rm -v /some/dir:/video
#	-p 9999:9999 -p 10000:10000 -p 10001:10001 -p 10002:10002 -p 11000:11000 -p 12000:12000 \
#	-p 13000:13000 -p 13001:13001 -p 13002:13002 -p 14000:14000 -p 15000:15000 -p 16000:16000 \
#	-p 17000:17000 -p 17001:17001 -p 17002:17002 -p 18000:18000 --name=voctocore bjoernr/voctomix core
## gui
## gui will connect to "corehost": corehost is aliased to container "voctocore"
# docker run -it --rm --env=gid=$(id -g) --env=uid=$(id -u) --env=DISPLAY=$DISPLAY --link=voctocore:corehost \
#   -v /tmp/.X11-unix:/tmp/.X11-unix -v /tmp/.docker.xauth:/tmp/. bjoernr/voctomix gui
## scripts
# docker run -it --rm bjoernr/voctomix --link=voctocore:corehost bjoernr/voctomix gstreamer/source-videotestsrc-as-background-loop.sh

FROM ubuntu:wily

MAINTAINER Bjoern Riemer <bjoern.riemer@web.de>

ENV DEBIAN_FRONTEND noninteractive

ENV uid 1000
ENV gid 1000

RUN useradd -m voc

RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		gstreamer1.0-plugins-bad gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
		gstreamer1.0-plugins-ugly gstreamer1.0-tools libgstreamer1.0-0 python3 python3-gi gir1.2-gstreamer-1.0 \
	&& apt-get install -y git wget \
	&& apt-get clean

# stuff for the GUI
RUN apt-get update \
	&& apt-get install -y gir1.2-gst-plugins-base-1.0 gir1.2-gstreamer-1.0 gir1.2-gtk-3.0 \
	ffmpeg \
	&& apt-get clean

RUN wget -q https://github.com/tianon/gosu/releases/download/1.7/gosu-amd64 -O /bin/gosu && chmod +x /bin/gosu
#RUN cd /opt && git clone https://github.com/voc/voctomix.git
RUN mkdir -p /opt/voctomix

EXPOSE 9998 9999 10000 10001 10002 11000 12000 13000 13001 13002 14000 15000 16000 17000 17001 17002 18000 
VOLUME /video

WORKDIR /opt/voctomix
COPY . /opt/voctomix/

RUN sed -i 's/localhost/corehost/g' voctogui/default-config.ini \
	&& find /opt/voctomix/example-scripts/ -type f -exec sed -i 's/localhost/corehost/g' {} \;

ENTRYPOINT ["/opt/voctomix/docker-ep.sh"]
CMD ["help"]