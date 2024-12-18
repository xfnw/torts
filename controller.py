#!/usr/bin/env python3

import re, io, os, sys, tarfile, argparse
from socket import AF_INET6
from functools import partial
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from requests_toolbelt.multipart.decoder import MultipartDecoder

from getsource import cache_src, expected_rel, get_relpath, format_changelog

NAMEPATTERN = re.compile(b'name="([^"]+)"', re.IGNORECASE)


class Handler(BaseHTTPRequestHandler):
    def __init__(self, package, script, *args, **kwargs):
        self.package = package
        self.script = script
        super().__init__(*args, **kwargs)

    def _ok(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(data)

    def _err(self):
        self.send_response(500)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"bonk bonk bonk bonk\n")

    def do_GET(self):
        self._ok(self.script)

    def do_POST(self):
        try:
            self._handle_upload()
        except Exception as e:
            print(e)
            self._err()

        sys.exit(0)

    def _handle_upload(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        ver = query["ver"][0]
        arch = query["arch"][0]

        prefix = f"result/{ver}.x/{arch}/tcz/"
        os.makedirs(prefix, exist_ok=True)

        contenttype = self.headers.get("Content-Type")
        length = int(self.headers.get("Content-Length"))
        data = self.rfile.read(length)

        for part in MultipartDecoder(data, contenttype).parts:
            disp = part.headers[b"Content-Disposition"]
            name = NAMEPATTERN.search(disp).group(1)

            filename = prefix + self.package

            match name:
                case b"tcz":
                    filename += ".tcz"
                case b"dep":
                    filename += ".tcz.dep"
                case b"md5":
                    filename += ".tcz.md5.txt"
                case b"info":
                    filename += ".tcz.info"
                case b"list":
                    filename += ".tcz.list"
                case b"zsync":
                    filename += ".tcz.zsync"
                case b"log":
                    filename += ".tcz.log"
                case _:
                    continue

            with open(filename, "wb") as f:
                f.write(part.content)

            print("got", filename)

        if "broken" in query:
            self._ok(b"package broken\n")
            return

        with open(get_relpath(self.package, ver, arch), "wb") as f:
            f.write(expected_rel(self.package, ver, arch))

        self._ok(b"nyaa~\n")


def create_script(package):
    with open("common.sh", "rb") as f:
        script = f.read()

    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w:gz") as t:
        t.add("pkgs/" + package, arcname=".")
        t.add("include")
        if srcpath := cache_src(package):
            t.add(srcpath, arcname="src")
        if changelog := format_changelog(package):
            changelog = changelog.encode("utf-8")
            info = tarfile.TarInfo(name="changelog")
            info.size = len(changelog)
            t.addfile(info, io.BytesIO(changelog))

    scrlen = script.count(b"\n") + 6
    tail = f"""
tail -n +{scrlen} $0 | tar xzf -
. ./TINYBUILD
__tinyports
sudo reboot -f
"""
    script += tail.encode("utf-8")

    script += archive.getvalue()

    return script


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bindhost", default="")
    parser.add_argument("--port", default=0, type=int)
    parser.add_argument("package")
    args = parser.parse_args()

    if not os.path.isfile("pkgs/" + args.package + "/TINYBUILD"):
        print(f"package {args.package} does not exist")
        sys.exit(1)

    script = create_script(args.package)

    if ":" in args.bindhost:
        HTTPServer.address_family = AF_INET6
    handler = partial(Handler, args.package, script)
    httpd = HTTPServer((args.bindhost, args.port), handler)
    (host, port, *_) = httpd.server_address
    if ":" in host:
        print(f"http://[{host}]:{port}", args.package)
    else:
        print(f"http://{host}:{port}", args.package)

    httpd.serve_forever()


if __name__ == "__main__":
    main()
