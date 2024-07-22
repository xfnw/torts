#!/usr/bin/env python3

import os, sys, json
from urllib.request import urlopen
from getsource import get_depends, ensure_exists, eprint


def walk(pkg, edges, parent=None):
    if pkg in edges:
        return
    ensure_exists(pkg, parent=parent)

    edges[pkg] = []

    for dep in get_depends(pkg):
        if len(dep) == 0 or dep[0] == "#":
            continue
        edges[pkg].append(dep)
        walk(dep, edges, parent=pkg)

def walkr(pkg, mirror, edges, parent=None):
    if pkg in edges:
        return

    edges[pkg] = []

    durl = mirror + f"/tcz/{pkg}.tcz.dep"
    eprint(durl)

    try:
        d = urlopen(durl, timeout=1)
    except Exception:
        return

    deps = d.read().decode("UTF-8").splitlines()

    for dep in deps:
        # 15.x x86 dbus.tcz.dep has a trailing space
        dep = dep.strip()
        if len(dep) == 0:
            continue
        if dep.endswith(".tcz"):
            dep = dep[:-4]
        edges[pkg].append(dep)
        walkr(dep, mirror, edges, parent=pkg)

def output(edges):
    print('digraph "torts" {')
    print("rankdir=LR;")
    for node, edge in edges.items():
        left = json.dumps(node)
        print(f"{left};")
        for right in edge:
            print(f"{left} -> {json.dumps(right)};")
    print("}")


def main():
    edges = dict()

    if len(sys.argv) > 1 and sys.argv[1] == "-r":
        if len(sys.argv) > 3:
            pkgs = sys.argv[3:]
        else:
            pkgs = os.listdir("pkgs")

        mirror = sys.argv[2].rstrip("/")

        for pkg in pkgs:
            walkr(pkg, mirror, edges)
    else:
        if len(sys.argv) > 1:
            pkgs = sys.argv[1:]
        else:
            pkgs = os.listdir("pkgs")

        for pkg in pkgs:
            walk(pkg, edges)

    output(edges)


if __name__ == "__main__":
    main()
