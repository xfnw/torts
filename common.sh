#!/bin/sh

. /etc/init.d/tc-functions

MAJORVER="$(getMajorVer)"
ARCH="$(getBuild)"
read MIRROR < /opt/tcemirror
MIRROR="${MIRROR%/}/$MAJORVER.x/$ARCH/tcz"

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
	if [ -x src/configure ]; then
		cd src
		./configure
	fi
}

buildPhase() {
	make -C src
}

checkPhase() {
	: doing nothing
}

installPhase() {
	make -C src install DESTDIR="$PWD/out"
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
}

uploadPhase() {
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

copyinfo() {
	wget -O "$pname.tcz.info" "$MIRROR/$1.tcz.info"
}

__broken() {
	tce-load -wil curl
	curl -X POST "$SCRIPT?ver=$MAJORVER&arch=$ARCH&broken=$1"
}

__tinyports() {
	: "building $pname"
	mkdir out
	(downloadPhase)
	(patchPhase)
	(configurePhase)
	(buildPhase)
	(checkPhase)
	(installPhase)
	(fixupPhase)
	(packagePhase)
	(metadataPhase)
	(submitPhase)
	(uploadPhase)
}

