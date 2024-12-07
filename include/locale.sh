downloadPhase() {
	tce-load -wil glibc_apps glibc_i18n_locale
}

buildPhase() {
	loc="${pname#*-}"

	sudo mkdir -p /usr/lib/locale
	sudo localedef -i "${loc%.*}" -c -f "${loc##*.}" "$loc"
}

installPhase() {
	mkdir -p out/usr/lib/locale
	cp -r /usr/lib/locale/locale-archive out/usr/lib/locale
}

metadataPhase() {
	version="$(ldd --version | head -n1)"
	version="${version##* }"
	cat - changelog > "$pname.tcz.info" <<EOF
Title:          $pname.tcz
Description:    pre-generated locale files for ${pname#*-}
Version:        ${version%.}
Author:         glibc locale authors
Original-site:  https://sourceware.org/glibc/
Copying-policy: LGPL-2.1-or-later
Size:           0
Extension_by:   xfnw
Tags:           locale support
Comments:       for when using getlocale.tcz is inconvenient,
                like on diskless systems
EOF
	cat > "$pname.tcz.dep" <<EOF
glibc_gconv.tcz
EOF
}
