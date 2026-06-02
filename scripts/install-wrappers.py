#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
import stat
from pathlib import Path


WRAPPERS = {
    "gcc": "cc.py",
    "cc": "cc.py",
    "g++": "cxx.py",
    "c++": "cxx.py",
    "ar": "ar.py",
    "gcc-ar": "ar.py",
    "ranlib": "ranlib.py",
    "gcc-ranlib": "ranlib.py",
    "nm": "nm.py",
    "gcc-nm": "nm.py",
    "ld": "ld.py",
    "objdump": "objdump.py",
    "readelf": "readelf.py",
    "strip": "strip.py",
}


def make_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def install_wrapper(src: Path, dst: Path) -> None:
    shutil.copy2(src, dst)
    make_executable(dst)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--bindir", type=Path, required=True)
    parser.add_argument("--wrappers-dir", type=Path, required=True)
    parser.add_argument("--enable-cxx", action="store_true")
    args = parser.parse_args()

    args.bindir.mkdir(parents=True, exist_ok=True)

    for suffix, wrapper_name in WRAPPERS.items():
        if suffix in {"g++", "c++"} and not args.enable_cxx:
            continue

        src = args.wrappers_dir / wrapper_name
        dst = args.bindir / f"{args.target}-{suffix}"
        install_wrapper(src, dst)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())