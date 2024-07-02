#!/usr/bin/env python3

import shlex, shutil, os
from hashlib import md5, file_digest
from subprocess import run
from tempfile import mkdtemp
from urllib.parse import urlparse


class Fetchers:
    def __init__(self):
        self.types = {
            "git+https": self.fetch_git_https,
            "git+http": self.fetch_git_http,
            "git": self.fetch_git,
            "tarball+https": self.fetch_tarball_https,
            "tarball+http": self.fetch_tarball_http,
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
        run(["git", "-C", target, "submodule", "update", "--init", "--depth=1"], check=True)

        shutil.rmtree(f"{target}/.git", ignore_errors=True)

    def fetch_tarball_http(self, url, target):
        self.fetch_tarball_https(url, target, scheme="http")

    def fetch_tarball_https(self, url, target, scheme="https"):
        ballpath = target + ".tar"
        hash = url.fragment
        if len(hash) < 64:
            raise Exception("sha256 required")
        url = url._replace(scheme=scheme, fragment="").geturl()

        run(["wget", "-O", ballpath, "--", url], check=True)

        with open(ballpath, "rb") as f:
            if (ohash := file_digest(f, "sha256").hexdigest()) != hash:
                raise Exception(f"hash mismatch: got {ohash} wanted {hash}")

        run(["tar", "xaf", ballpath, "-C", target, "--strip-components=1"], check=True)

        os.remove(ballpath)


def get_relpath(pkg, tcver, arch):
    return f"result/{tcver}.x/{arch}/tcz/{pkg}.tcz.build"


def get_depends(pkg):
    reqname = "pkgs/" + pkg + "/DEPENDS"
    if os.path.isfile(reqname):
        with open(reqname, "r") as reqs:
            return reqs.read().splitlines()
    return []


def get_tinybuild_var(pkg, var):
    var += "="
    val = None
    with open(f"pkgs/{pkg}/TINYBUILD", "r") as f:

        for part in shlex.split(f.read(), comments=True):
            if part.startswith(var):
                val = part.split("=", 1)[1]
                break

    return val


def hash_src(uri):
    return md5(uri.encode("utf-8")).hexdigest()


def cache_src(pkg, no_fetch=False):
    uri = get_tinybuild_var(pkg, "src")
    if uri is None:
        return None
    hash = hash_src(uri)
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


def expected_rel(pkg, tcver, arch):
    uri = get_tinybuild_var(pkg, "src")
    if uri is None:
        hash = "0" * 32
    else:
        hash = hash_src(uri)
    rel = get_tinybuild_var(pkg, "rel") or 0
    out = f"{hash}-{rel}\n".encode("utf-8")
    for dep in get_depends(pkg):
        if len(dep) == 0 or dep[0] == "#":
            continue
        deppath = get_relpath(dep, tcver, arch)
        if not os.path.isfile(deppath):
            out += b"missing dependency?\n"
            continue
        with open(deppath, "rb") as f:
            out += f.read()
    return out


def needs_rebuild(pkg, tcver, arch):
    expect = expected_rel(pkg, tcver, arch)
    relpath = get_relpath(pkg, tcver, arch)
    if not os.path.isfile(relpath):
        return True
    with open(relpath, "rb") as f:
        if f.read() != expect:
            return True
    return False


def is_broken(pkg, tcver, arch):
    broken = get_tinybuild_var(pkg, "broken")
    if broken is None:
        return False

    for brok in broken.split():
        if len(brok) > 1:
            lo, sep, hi = brok.partition("..")
            if sep:
                if hi:
                    hi = int(hi[1:]) + 1 if hi[0] == "=" else int(hi)
                if (not lo or tcver >= int(lo)) and (not hi or tcver < hi):
                    return True
                continue
        if brok.isdigit() and tcver == int(brok) or arch == brok:
            return True

    return False
