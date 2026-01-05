#!/usr/bin/env python3

import argparse
import sys
from urllib.parse import urlparse

def normalize_host(url: str) -> str:
    url = url.strip()
    if not url:
        return None

    # Add scheme if missing (required for urlparse)
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    parsed = urlparse(url)
    host = parsed.netloc.lower()

    # Remove default ports
    if host.endswith(":80"):
        host = host[:-3]
    elif host.endswith(":443"):
        host = host[:-4]

    return host


def read_urls(source):
    if source == "-":
        return sys.stdin.read().splitlines()
    with open(source, "r", encoding="utf-8") as f:
        return f.read().splitlines()


def main():
    parser = argparse.ArgumentParser(
        description="Normalize URLs to hostnames only"
    )
    parser.add_argument("-u", "--url", help="Single URL")
    parser.add_argument("-f", "--file", help="File with URLs (or '-' for stdin)")
    args = parser.parse_args()

    urls = []
    if args.url:
        urls.append(args.url)
    if args.file:
        urls.extend(read_urls(args.file))

    if not urls:
        parser.error("Provide --url or --file")

    hosts = {normalize_host(u) for u in urls if normalize_host(u)}

    for h in sorted(hosts):
        print(h)


if __name__ == "__main__":
    main()
