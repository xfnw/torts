#!/bin/sh

. /etc/init.d/tc-functions

FULLVER="$(getFullVer)"
MAJORVER="${FULLVER%.*}"
ARCH="$(getBuild)"
broken=

for arg in $(cat /proc/cmdline); do
	case "$arg" in
		script=*)
			SCRIPT="$(printf %s "${arg#*=}")"
			;;
	esac
done

trap '__broken trapped' EXIT

set -eux

downloadPhase() {
	: doing nothing
}

patchPhase() {
	: doing nothing
}

configurePhase() {
	: doing nothing
}

buildPhase() {
	: doing nothing
}

checkPhase() {
	: doing nothing
}

installPhase() {
	: doing nothing
}

fixupPhase() {
	tce-load -wil findutils sstrip
	find out -type f -executable -exec sstrip -z {} \;
}

packagePhase() {
	tce-load -wil squashfs-tools
	mksquashfs out "$pname.tcz" -noappend
}

metadataPhase() {
	: doing nothing
}

submitPhase() {
	tce-load -wil submitqc
	submitqc -c --libs --fix --strip "$pname.tcz"

	dep= info= list= zsync=
	[ -e "$pname.tcz.dep" ] && dep="-Fdep=@$pname.tcz.dep"
	[ -e "$pname.tcz.info" ] && info="-Finfo=@$pname.tcz.info"
	[ -e "$pname.tcz.list" ] && list="-Flist=@$pname.tcz.list"
	[ -e "$pname.tcz.zsync" ] && zsync="-Fzsync=@$pname.tcz.zsync"

	tce-load -wil curl
	# XXX: intentionally unquoted
	curl "-Ftcz=@$pname.tcz" "-Fmd5=@$pname.tcz.md5.txt" $dep $info $list $zsync \
		"$SCRIPT?ver=$MAJORVER&arch=$ARCH"
}

__broken(){
	tce-load -wil curl
	curl -X POST "$SCRIPT?ver=$MAJORVER&arch=$ARCH&broken=$1"
}

__tinyports() {
	: "building $pname v$version"
	if [ "$broken" != "${broken#*"$FULLVER"}" ]; then
		__broken marked
		return
	fi
	mkdir out
	downloadPhase
	patchPhase
	configurePhase
	buildPhase
	checkPhase
	installPhase
	fixupPhase
	packagePhase
	metadataPhase
	submitPhase
}

