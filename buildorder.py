#!/usr/bin/env python3

import os, sys
from getsource import needs_rebuild, is_broken


def eprint(*yip, **yap):
    print(*yip, file=sys.stderr, **yap)


def ensure_exists(pkg, parent=None):
    if not os.path.isfile("pkgs/" + pkg + "/TINYBUILD"):
        eprint("missing package", pkg)
        if parent:
            eprint("depended on by", parent)
        sys.exit(1)


def rebuilds(pkg, visited, rebuilded, tcver, arch, parent=None):
    if pkg in rebuilded:
        return True
    if pkg in visited:
        return False
    ensure_exists(pkg, parent=parent)
    visited.add(pkg)

    if is_broken(pkg, tcver, arch):
        return False
    if needs_rebuild(pkg, tcver, arch):
        rebuilded.add(pkg)
        print(pkg)
        return True

    reqname = "pkgs/" + pkg + "/DEPENDS"
    if os.path.isfile(reqname):
        with open(reqname, "r") as reqs:
            for dep in reqs.read().splitlines():
                if len(dep) == 0 or dep[0] == "#":
                    continue
                if rebuilds(dep, visited, rebuilded, tcver, arch, parent=pkg):
                    rebuilded.add(pkg)
                    print(pkg)
                    return True

    return False


def main():
    if len(sys.argv) <= 2:
        print("usage: tcver arch")
        return

    tcver = sys.argv[1]
    arch = sys.argv[2]
    visited = set()
    rebuilded = set()

    for pkg in os.listdir("pkgs"):
        rebuilds(pkg, visited, rebuilded, tcver, arch)
    return


if __name__ == "__main__":
    main()
