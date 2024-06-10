#!/usr/bin/env python3

import shlex, shutil, os
from hashlib import md5
from subprocess import run
from tempfile import mkdtemp
from urllib.parse import urlparse


class Fetchers:
    def __init__(self):
        self.types = {"git+https": self.fetch_git_https}

    def fetch(self, url, target, name):
        purl = urlparse(url)
        fetcher = self.types[purl.scheme]

        tmp = mkdtemp()
        subtmp = f"{tmp}/{name}"
        # subdir nonsense because shutil.move
        # does not allow specifying the name
        os.mkdir(subtmp)
        fetcher(purl, subtmp)

        shutil.move(subtmp, target)
        os.rmdir(tmp)

    def fetch_git_https(self, url, target):
        rev = url.fragment
        if len(rev) < 40:
            raise Exception("full git rev required")
        url = url._replace(scheme="https", fragment="").geturl()

        run(["git", "-C", target, "init"], check=True)
        run(["git", "-C", target, "remote", "add", "origin", "--", url], check=True)
        run(
            ["git", "-C", target, "fetch", "--depth=1", "origin", "--", f"{rev}:build"],
            check=True,
        )
        run(["git", "-C", target, "checkout", "build"], check=True)

        shutil.rmtree(f"{target}/.git", ignore_errors=True)


def get_src_uri(pkg):
    src = None
    with open(f"pkgs/{pkg}/TINYBUILD", "r") as f:

        for part in shlex.split(f.read()):
            if part.startswith("src="):
                src = part.split("=", 1)[1]
                break

    return src


def cache_src(pkg):
    uri = get_src_uri(pkg)
    if uri is None:
        return None
    hash = md5(uri.encode("utf-8")).hexdigest()
    path = f"cache/{hash[:2]}"
    fullpath = f"{path}/{hash[2:]}"
    if os.path.isdir(fullpath):
        return fullpath
    os.makedirs(path, exist_ok=True)

    fetcher = Fetchers()
    fetcher.fetch(uri, path, hash[2:])
    return fullpath
