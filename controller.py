#!/usr/bin/env python3

import re, os, sys, argparse
from functools import partial
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from requests_toolbelt.multipart.decoder import MultipartDecoder

NAMEPATTERN = re.compile(b'name="([^"]+)"', re.IGNORECASE)


class Handler(BaseHTTPRequestHandler):
    def __init__(self, package, common, *args, **kwargs):
        self.package = package
        self.common = common
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
        self._handle_script()

    def _handle_script(self):
        script = self.common
        with open("pkgs/" + self.package + "/TINYBUILD", "rb") as f:
            script += f.read()
        script += b"\n__tinyports\n"

        self._ok(script)

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
                case _:
                    continue

            with open(filename, "wb") as f:
                f.write(part.content)

            print("got", filename)

        self._ok(b"nyaa~\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bindhost", default="")
    parser.add_argument("--port", default=0, type=int)
    parser.add_argument("package")
    args = parser.parse_args()

    with open("common.sh", "rb") as f:
        common = f.read()

    if not os.path.isfile("pkgs/" + args.package + "/TINYBUILD"):
        print(f"package {args.package} does not exist")
        sys.exit(1)

    handler = partial(Handler, args.package, common)
    httpd = HTTPServer((args.bindhost, args.port), handler)
    (host, port) = httpd.server_address
    if ":" in host:
        print(f"http://[{host}]:{port}")
    else:
        print(f"http://{host}:{port}")

    httpd.serve_forever()


if __name__ == "__main__":
    main()
