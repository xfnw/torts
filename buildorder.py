#!/usr/bin/env python3

import os, sys
from getsource import needs_rebuild


def eprint(*yip, **yap):
    print(*yip, file=sys.stderr, **yap)


def ensure_exists(pkg, parent=None):
    if not os.path.isfile("pkgs/" + pkg + "/TINYBUILD"):
        eprint("missing package", pkg)
        if parent:
            eprint("depended on by", parent)
        sys.exit(1)


def depends(pkg, visited, parent=None):
    if pkg in visited:
        return
    ensure_exists(pkg, parent=parent)

    visited.add(pkg)
    reqname = "pkgs/" + pkg + "/DEPENDS"
    if os.path.isfile(reqname):
        with open(reqname, "r") as reqs:
            for dep in reqs.read().splitlines():
                if len(dep) == 0 or dep[0] == "#":
                    continue
                depends(dep, visited, parent=pkg)

    print(pkg)


def rebuilds(pkg, visited, rebuilded, parent=None):
    if pkg in rebuilded:
        return True
    if pkg in visited:
        return False
    ensure_exists(pkg, parent=parent)

    if needs_rebuild(pkg):
        rebuilded.add(pkg)
        print(pkg)
        return True

    visited.add(pkg)
    reqname = "pkgs/" + pkg + "/DEPENDS"
    if os.path.isfile(reqname):
        with open(reqname, "r") as reqs:
            for dep in reqs.read().splitlines():
                if len(dep) == 0 or dep[0] == "#":
                    continue
                if rebuilds(dep, visited, rebuilded, parent=pkg):
                    rebuilded.add(pkg)
                    print(pkg)
                    return True

    return False


def main():
    visited = set()

    if len(sys.argv) > 1 and sys.argv[1] == "r":
        rebuilded = set()
        for pkg in os.listdir("pkgs"):
            rebuilds(pkg, visited, rebuilded)
        return

    for pkg in os.listdir("pkgs"):
        depends(pkg, visited)


if __name__ == "__main__":
    main()
