#!/bin/sh

source /etc/init.d/tc-functions

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
	: doing nothing
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

	for arg in $(cat /proc/cmdline); do
		case "$arg" in
			script=*)
				SCRIPT="$(printf %s "${arg#*=}")"
				;;
		esac
	done

	dep= info=
	[ -e "$pname.tcz.dep" ] && dep="-Fdep=@$pname.tcz.dep"
	[ -e "$pname.tcz.info" ] && info="-Finfo=@$pname.tcz.info"

	tce-load -wil curl
	# XXX: dep and info intentionally unquoted
	curl "-Ftcz=@$pname.tcz" "-Fmd5=@$pname.tcz.md5.txt" $dep $info \
		"$SCRIPT?ver=$(getMajorVer)&arch=$(getBuild)"
}

__tinyports() {
	: "building $pname v$version"
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

