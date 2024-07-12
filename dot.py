#!/usr/bin/env python3

import os, sys, json
from getsource import get_depends, ensure_exists


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
    if len(sys.argv) > 1:
        pkgs = sys.argv[1:]
    else:
        pkgs = os.listdir("pkgs")

    edges = dict()

    for pkg in pkgs:
        walk(pkg, edges)

    output(edges)


if __name__ == "__main__":
    main()
