#!/bin/bash
##
## entrypoint for the docker images

if [ ! -f /.dockerenv ] && [ ! -f /.dockerinit ]; then
	echo "WARNING: this scrip should be only runed inside docker!!"
	exit 1
fi

if [ ! -z $gid ] && [ ! -z $uid ]; then
	groupmod -g $gid voc
	usermod -u $uid -g $gid voc

	# check if homedir is mounted
	if grep -q '/home/voc' /proc/mounts; then
		# homedir is mounted into the docker so don't touch the ownership of the files
		true
	else
		# fixup for changed uid and gid
		chown -R voc:voc /home/voc
	fi
fi

function startCore() {
	echo "Starting Voctomix CORE"
	if [ -x /bin/gosu ]; then
		gosu voc /opt/voctomix/voctocore/voctocore.py -v
	else
		echo "no gosu found..."
		exec su -l -c "/opt/voctomix/voctocore/voctocore.py -v" voc
	fi
}

function isVideoMounted() {
	return grep -q '/video' /proc/mounts
}

function startGui() {
	echo "Starting Voctomix GUI..."
	if [ -x /bin/gosu ]; then
		gosu voc /opt/voctomix/voctogui/voctogui.py -v
	else
		echo "no gosu found..."
		exec su -l -c "/opt/voctomix/voctogui/voctogui.py -v" voc
	fi
}

function listExamples() {
	cd example-scripts/
	find  -type f
}

function runExample() {
	if [ -z $1 ]; then 
		echo "no valid example! "
	fi
	FILENAME="example-scripts/$1"
	if [ -f ${FILENAME} ]; then
		echo "Running: ${FILENAME}"
		${FILENAME}
	fi
}

function usage() {
	echo "Usage: $0 <cmd>"
	echo "help			- this text"
	echo "core 			- starts voctomix gore"
	echo "gui 			- starts the voctomix GUI"
	echo "examples	 	- lists the example scripts"
	echo "bash			- run interactive bash"
	echo "scriptname.py - starts the example script named 'scriptname.py' "
}

if [ -z $1 ]; then
	usage
	exit
fi

case $1 in
	help )
		usage
		;;
	examples )
		listExamples
		;;
	gui )
		startGui
		;;
	core )
		startCore
		;;
	bash )
		shift 
		bash $@
		;;
	* )
		runExample $1
		;;
esac
