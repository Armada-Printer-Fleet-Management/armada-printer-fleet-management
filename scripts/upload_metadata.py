#!/usr/bin/env python3
"""Prints the CreatePrintJobUpload request body for a file, with its size and sha256 filled in.

Usage:
    python scripts/upload_metadata.py <path> [--file-type {gcode,cgcode}]

Paste the output into Bruno's Create Print Job Upload request, then send the same file as the
body of Upload File.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

FILE_TYPES = {"gcode": "FILE_TYPE_GCODE", "cgcode": "FILE_TYPE_CGCODE"}
CHUNK_SIZE = 1024 * 1024


def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def request_body(path: pathlib.Path, file_type: str) -> dict[str, object]:
    return {
        # Left for Bruno to fill in from the environment.
        "printJobId": {"value": "{{printJobId}}"},
        "metadata": {
            "filename": path.name,
            # proto3 JSON writes 64-bit integers as strings.
            "sizeBytes": str(path.stat().st_size),
            "sha256": sha256_of(path),
            "fileType": FILE_TYPES[file_type],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prints the CreatePrintJobUpload request body for a file."
    )
    parser.add_argument("path", type=pathlib.Path, help="the file to upload")
    parser.add_argument(
        "--file-type",
        choices=FILE_TYPES,
        default="gcode",
        help="gcode for plain-text G-code, cgcode for compressed or binary G-code (default: gcode)",
    )
    args = parser.parse_args()
    path: pathlib.Path = args.path
    if not path.is_file():
        print(f"error: no file at {path}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(request_body(path, args.file_type), indent=2))


if __name__ == "__main__":
    main()
