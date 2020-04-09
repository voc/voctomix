#!/usr/bin/env bash
##
## entrypoint for the docker images

if [ ! -f /.dockerenv ] && [ ! -f /.dockerinit ]; then
  >&2 echo "WARNING: this script should be only run inside docker!!"
  exit 1
fi

# shellcheck disable=SC2154
if [[ ! -z $gid ]] && [[ ! -z $uid ]]; then
  groupmod -g "${gid}" voc
  usermod -u "${uid}" -g "${gid}" voc

  # check if homedir is mounted
  if ! grep -q '/home/voc' /proc/mounts; then
    # fixup for changed uid and gid
    chown -R voc:voc /home/voc
  fi
fi

start_core() {
  >&2 echo "Starting VoctoMix Core"

  if [[ -x /bin/gosu ]]; then
    gosu voc /opt/voctomix/voctocore/voctocore.py -v
  else
    >&2 echo "no gosu binary found..."
    exec su -l -c "/opt/voctomix/voctocore/voctocore.py -v" voc
  fi
}

is_video_mounted() {
    grep -q '/video' /proc/mounts
}

start_gui() {
  >&2 echo "Starting VoctoMix GUI..."

  if [[ -x /bin/gosu ]]; then
    gosu voc /opt/voctomix/voctogui/voctogui.py -v
  else
    >&2 echo "no gosu binary found..."
    exec su -l -c "/opt/voctomix/voctogui/voctogui.py -v" voc
  fi
}

list_examples() {
  cd example-scripts/
  find -type f
}

run_example() {
    if [ -z $1 ]; then
      echo "no valid example!"
    fi

    FILENAME="example-scripts/$1"
    if [[ -f ${FILENAME} ]]; then
      >&2 echo "Running: ${FILENAME}"
      ${FILENAME}
    fi
}

usage() {
    cat <<-USAGE
Usage: $0 <cmd>

Program for starting voctomix

COMMANDS:

  help          - this text
  core          - starts voctomix core
  gui           - starts voctomix GUI
  examples      - lists the example scripts
  console       - run interactive console
  scriptname.py - starts the example script named 'scriptname.py'
USAGE
}

if [[ $# -le 0 ]]; then
  usage
  exit 1
fi

case $1 in
  help )
    usage
    exit 1
    ;;
  examples )
    list_examples
    exit 0
    ;;
  gui)
    start_gui
    exit 0
    ;;
  core)
    start_core
    exit 0
    ;;
  bash)
    shift 
    bash "$@"
    exit 0
    ;;
  *)
    run_example "$1"
    exit 0
    ;;
esac
