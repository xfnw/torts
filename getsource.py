#!/usr/bin/env python3

import shlex, shutil, os
from hashlib import md5
from subprocess import run
from tempfile import mkdtemp
from urllib.parse import urlparse


class Fetchers:
    def __init__(self):
        self.types = {
            "git+https": self.fetch_git_https,
            "git+http": self.fetch_git_http,
            "git": self.fetch_git,
        }

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
        self.fetch_git(url, target, scheme="https")

    def fetch_git_http(self, url, target):
        self.fetch_git(url, target, scheme="http")

    def fetch_git(self, url, target, scheme="git"):
        rev = url.fragment
        if len(rev) < 40:
            raise Exception("full git rev required")
        url = url._replace(scheme=scheme, fragment="").geturl()

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


def cache_src(pkg, no_fetch=False):
    uri = get_src_uri(pkg)
    if uri is None:
        return None
    hash = md5(uri.encode("utf-8")).hexdigest()
    path = f"cache/{hash[:2]}"
    fullpath = f"{path}/{hash[2:]}"
    if os.path.isdir(fullpath):
        return fullpath
    os.makedirs(path, exist_ok=True)

    if no_fetch:
        return False

    fetcher = Fetchers()
    fetcher.fetch(uri, path, hash[2:])
    return fullpath


def needs_rebuild(pkg):
    if cache_src(pkg, no_fetch=True) == False:
        return True
    return False
