#!/usr/bin/env python3

import os, sys


def eprint(*yip, **yap):
    print(*yip, file=sys.stderr, **yap)


def depends(pkg, visited, parent=None):
    if pkg in visited:
        return
    if not os.path.isfile("pkgs/" + pkg + "/TINYBUILD"):
        eprint("missing package", pkg)
        if parent:
            eprint("depended on by", parent)
        sys.exit(1)

    visited.add(pkg)
    reqname = "pkgs/" + pkg + "/DEPENDS"
    if os.path.isfile(reqname):
        with open(reqname, "r") as reqs:
            for dep in reqs.read().splitlines():
                if len(dep) == 0 or dep[0] == "#":
                    continue
                depends(dep, visited, parent=pkg)

    print(pkg)


def main():
    visited = set()
    for pkg in os.listdir("pkgs"):
        depends(pkg, visited)


if __name__ == "__main__":
    main()
