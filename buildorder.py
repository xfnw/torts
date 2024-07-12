#!/usr/bin/env python3

import os, sys
from getsource import needs_rebuild, is_broken, get_depends, ensure_exists


def rebuilds(pkg, state, tcver, arch, parent=None):
    if pkg in state:
        return state[pkg]
    ensure_exists(pkg, parent=parent)

    if is_broken(pkg, tcver, arch):
        state[pkg] = 2
        return 2

    myret = 0
    for dep in get_depends(pkg):
        if len(dep) == 0 or dep[0] == "#":
            continue
        if ret := rebuilds(dep, state, tcver, arch, parent=pkg):
            myret = max(myret, ret)
            if ret >= 2:
                break

    if myret == 0 and needs_rebuild(pkg, tcver, arch):
        myret = 1
    if myret == 1:
        print(pkg)
    state[pkg] = myret
    return myret


def main():
    if len(sys.argv) <= 2:
        print("usage: tcver arch")
        return

    tcver = int(sys.argv[1])
    arch = sys.argv[2]
    state = dict()

    for pkg in os.listdir("pkgs"):
        rebuilds(pkg, state, tcver, arch)
    return


if __name__ == "__main__":
    main()
