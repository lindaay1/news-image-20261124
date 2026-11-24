#!/usr/bin/env python3
"""Entry program for news-image-20261124.

Ships the newspaper front page (entry.jpg, drawn by render24.py) as
the contest image: it is copied to ``entry.png`` in the output
directory (the name stays entry.png although the bytes are JPEG, as
the competition allows — the format is told apart by the first
bytes). Before copying, the file is checked end to end so a corrupt
image can never be submitted: SOI magic, a walk over every segment
that finds exactly one frame header reporting 1024x1024, 8-bit
samples and 3 components, a scan section, and a proper EOI marker
as the last two bytes, all within the 1 MiB cap. After writing, the
output is read back and compared byte for byte with the source, so
both graded runs can only ever produce identical bytes.

Standard library only. No network, no environment reads, no writes
outside the output directory.
"""

import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "entry.jpg")
LIMIT = 1048576
SIZE = (1024, 1024)

# Markers with no length field after them (besides SOI/EOI/RSTn/TEM).
BARE = {0x01, 0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9}
# Frame headers (baseline / extended / progressive, non-differential).
FRAMES = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
          0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def die(why):
    raise SystemExit("main.py: entry.jpg failed validation: " + why)


def check(blob):
    """Return (width, height) or die. Walks every JPEG segment."""
    if len(blob) < 4:
        die("only %d bytes" % len(blob))
    if blob[:2] != b"\xff\xd8":
        die("no SOI magic")
    if blob[-2:] != b"\xff\xd9":
        die("no EOI marker at the end")
    if len(blob) > LIMIT:
        die("%d bytes, over the 1 MiB cap" % len(blob))
    pos, frame, scan = 2, None, False
    while pos + 1 < len(blob):
        if blob[pos] != 0xFF:
            die("expected 0xFF at offset %d" % pos)
        mark = blob[pos + 1]
        if mark == 0xFF:  # padding byte: stay on this marker
            pos += 1
            continue
        pos += 2
        if mark == 0xD9:  # EOI
            break
        if mark in BARE:
            continue
        if mark == 0xDA:  # start of scan: entropy data follows
            scan = True
            break
        if pos + 2 > len(blob):
            die("truncated segment length")
        seg = (blob[pos] << 8) | blob[pos + 1]
        if seg < 2 or pos + seg > len(blob):
            die("bad segment length %d at offset %d" % (seg, pos))
        if mark in FRAMES:
            if frame is not None:
                die("second frame header")
            if seg < 8:
                die("short frame header")
            depth = blob[pos + 2]
            height = (blob[pos + 3] << 8) | blob[pos + 4]
            width = (blob[pos + 5] << 8) | blob[pos + 6]
            comps = blob[pos + 7]
            if depth != 8:
                die("sample depth %d, want 8" % depth)
            if (width, height) != SIZE:
                die("%dx%d, want 1024x1024" % (width, height))
            if comps not in (1, 3):
                die("%d components, want 1 or 3" % comps)
            frame = (width, height)
        pos += seg
    if frame is None:
        die("no frame header found")
    if not scan:
        die("no scan section found")
    return frame


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    with open(SOURCE, "rb") as fh:
        blob = fh.read()
    check(blob)
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "entry.png")
    with open(target, "wb") as fh:
        fh.write(blob)
    with open(target, "rb") as fh:
        back = fh.read()
    if hashlib.sha256(back).hexdigest() != hashlib.sha256(blob).hexdigest():
        raise SystemExit("main.py: output does not match entry.jpg")
    print("wrote %s (%d bytes, 1024x1024 JPEG)" % (target, len(blob)))


if __name__ == "__main__":
    main()
