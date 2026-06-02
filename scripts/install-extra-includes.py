#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree_merge(src_dir: Path, dst_dir: Path) -> None:
    if not src_dir.exists():
        raise RuntimeError(f"include directory does not exist: {src_dir}")

    if not src_dir.is_dir():
        raise RuntimeError(f"include path is not a directory: {src_dir}")

    for src in src_dir.rglob("*"):
        rel = src.relative_to(src_dir)
        dst = dst_dir / rel

        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue

        if src.is_symlink():
            dst.parent.mkdir(parents=True, exist_ok=True)

            if dst.exists() or dst.is_symlink():
                if dst.is_dir() and not dst.is_symlink():
                    shutil.rmtree(dst)
                else:
                    dst.unlink()

            target = src.readlink()
            dst.symlink_to(target)
            continue

        if src.is_file():
            copy_file(src, dst)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install additional toolchain headers into the sysroot"
    )

    parser.add_argument(
        "--include-dir",
        type=Path,
        required=True,
        help="Source include directory to install",
    )

    parser.add_argument(
        "--sysroot",
        type=Path,
        required=True,
        help="Target sysroot",
    )

    parser.add_argument(
        "--dest-subdir",
        default="usr/include",
        help="Destination inside sysroot, default: usr/include",
    )

    args = parser.parse_args()

    include_dir = args.include_dir.resolve()
    dst_dir = args.sysroot.resolve() / args.dest_subdir

    dst_dir.mkdir(parents=True, exist_ok=True)
    copy_tree_merge(include_dir, dst_dir)

    print(f"Installed extra includes:")
    print(f"  from: {include_dir}")
    print(f"  to:   {dst_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())