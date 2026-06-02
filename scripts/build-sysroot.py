#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.process import run


DEFAULT_MUSL_GIT_URL = "https://github.com/wasm-system-platform/musl-wasp.git"


def ensure_musl_source(
    *,
    musl_src: Path | None,
    download_dir: Path,
    git_url: str,
    git_ref: str | None,
    update: bool,
) -> Path:
    if musl_src is not None:
        musl_src = musl_src.resolve()
        if not (musl_src / "configure").exists():
            raise RuntimeError(f"musl source does not look valid: {musl_src}")
        return musl_src

    download_dir.mkdir(parents=True, exist_ok=True)
    dst = download_dir / "musl-wasp"

    if not dst.exists():
        run(["git", "clone", git_url, dst])
    elif update:
        run(["git", "fetch", "--tags", "--prune"], cwd=dst)

    if git_ref:
        run(["git", "checkout", git_ref], cwd=dst)
    elif update:
        run(["git", "pull", "--ff-only"], cwd=dst)

    if not (dst / "configure").exists():
        raise RuntimeError(f"downloaded musl source does not look valid: {dst}")

    return dst.resolve()


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument("--musl-src", type=Path)
    parser.add_argument("--musl-git-url", default=DEFAULT_MUSL_GIT_URL)
    parser.add_argument("--musl-ref")
    parser.add_argument("--musl-update", action="store_true")

    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--sysroot", type=Path, required=True)
    parser.add_argument("--bindir", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--jobs", type=int, required=True)

    args = parser.parse_args()

    musl_src = ensure_musl_source(
        musl_src=args.musl_src,
        download_dir=args.build_dir.parent / "sources",
        git_url=args.musl_git_url,
        git_ref=args.musl_ref,
        update=args.musl_update,
    )

    if args.build_dir.exists():
        shutil.rmtree(args.build_dir)

    args.build_dir.mkdir(parents=True)

    env = os.environ.copy()
    env.update(
        {
            "CC": str(args.bindir / f"{args.target}-cc"),
            "AR": str(args.bindir / f"{args.target}-ar"),
            "RANLIB": str(args.bindir / f"{args.target}-ranlib"),
        }
    )

    run(
        [
            musl_src / "configure",
            f"CROSS_COMPILE={args.bindir}/{args.target}-",
            f"--target={args.target}",
            "--prefix=/usr",
            "--syslibdir=/usr/lib",
            "--disable-shared",
        ],
        cwd=args.build_dir,
        env=env,
    )

    run(["make", f"-j{args.jobs}"], cwd=args.build_dir, env=env)
    run(["make", f"DESTDIR={args.sysroot}", "install"], cwd=args.build_dir, env=env)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())