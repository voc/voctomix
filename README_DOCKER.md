# HowTo use the Docker version of Voctomix
## build the docker container locally
- checkout branch: 
```
git checkout quickstart-docker
```
- build docker
```
docker build -t local/voctomix .
```
- rebuild docker after changes
```
docker tag local/voctomix:latest local/voctomix:old; \
docker build -t local/voctomix . && docker rmi local/voctomix:old
```

## Test the docker
the entrypoint script of the container provides some commands to ease the startup of the individual components. get a list by running
```docker run --rm -it --name=voctocore local/voctomix core```

## Run the components
### CORE
```
docker run --rm -it --name=voctocore local/voctomix core
```
### Source example scripts
```
docker run -it --rm --name=cam1 --link=voctocore:corehost local/voctomix ./gstreamer/source-videotestsrc-as-cam1.sh
docker run -it --rm --name=bg --link=voctocore:corehost local/voctomix gstreamer/source-videotestsrc-as-background-loop.sh
```

### GUI
to run the GUI in a docker the docker user needs access to the local X server. This is done by sharing the ```/tmp/.X11-unix``` socket with the container. Depending on your X11 setup you have to allow access to the X-Server session by running: ```xhost +local:$(id -un)```
The example below maps the local voctogui config file ```/tmp/vocto/configgui.ini``` into the container. Please create and change this file to change the voctogui configuration.
```
docker run -it --rm --name=gui --env=gid=$(id -g) --env=uid=$(id -u) --env=DISPLAY=:0 --link=voctocore:corehost \
  -v /tmp/vocto/configgui.ini:/opt/voctomix/voctogui/config.ini -v /tmp/.X11-unix:/tmp/.X11-unix -v /tmp/.docker.xauth:/tmp/.docker.xauth local/voctomix gui
```
