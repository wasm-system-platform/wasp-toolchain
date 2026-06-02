#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.process import require_tool, run


DEFAULT_MUSL_GIT_URL = "https://github.com/wasm-system-platform/musl-wasp.git"

def main() -> int:
    this_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser()

    parser.add_argument("--out", type=Path, default="out")
    parser.add_argument("--build", type=Path, default="build")

    parser.add_argument("--musl-src", type=Path)
    parser.add_argument("--musl-git-url", default=DEFAULT_MUSL_GIT_URL)
    parser.add_argument("--musl-ref")
    parser.add_argument("--musl-update", action="store_true")

    parser.add_argument("--llvm-src", type=Path)
    parser.add_argument("--llvm-target", default="wasm32-unknown-unknown")

    parser.add_argument("--download-dir", type=Path)
    parser.add_argument("--target", default="wasm32-wasp-linux")
    parser.add_argument("--clang", default=os.environ.get("CLANG", "clang"))
    parser.add_argument("--clangxx", default=os.environ.get("CLANGXX", "clang++"))
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--enable-cxx", action="store_true")

    args = parser.parse_args()

    required_tools = [
        args.clang,
        "cmake",
        "ninja",
        "make",
        "llvm-ar",
        "llvm-ranlib",
        "llvm-nm",
        "llvm-objdump",
        "llvm-readelf",
        "wasm-ld",
    ]

    if args.musl_src is None:
        required_tools.append("git")

    for tool in required_tools:
        require_tool(tool)

    out = args.out.resolve()
    build = args.build.resolve()
    bindir = out / "bin"
    sysroot = out / args.target / "sysroot"

    bindir.mkdir(parents=True, exist_ok=True)
    (sysroot / "usr/include").mkdir(parents=True, exist_ok=True)
    (sysroot / "usr/lib").mkdir(parents=True, exist_ok=True)
    build.mkdir(parents=True, exist_ok=True)

    wrapper_env = os.environ.copy()
    wrapper_env.update(
        {
            "WASP_TOOLCHAIN_TARGET": args.target,
            "WASP_LLVM_TARGET": args.llvm_target,
            "HOST_CLANG": args.clang,
            "HOST_CLANGXX": args.clangxx,
        }
    )

    run(
        [
            sys.executable,
            this_dir / "scripts/install-wrappers.py",
            "--target", args.target,
            "--bindir", bindir,
            "--wrappers-dir", this_dir / "wrappers",
            *(["--enable-cxx"] if args.enable_cxx else []),
        ],
        env=wrapper_env,
    )

    build_sysroot_cmd = [
        sys.executable,
        this_dir / "scripts/build-sysroot.py",
        "--build-dir", build / "musl",
        "--sysroot", sysroot,
        "--bindir", bindir,
        "--target", args.target,
        "--jobs", str(args.jobs),
        "--musl-git-url", args.musl_git_url,
    ]

    if args.musl_src is not None:
        build_sysroot_cmd.extend(["--musl-src", args.musl_src.resolve()])

    if args.musl_ref is not None:
        build_sysroot_cmd.extend(["--musl-ref", args.musl_ref])

    if args.musl_update:
        build_sysroot_cmd.append("--musl-update")

    if args.download_dir is not None:
        build_sysroot_cmd.extend(["--download-dir", args.download_dir.resolve()])

    run(build_sysroot_cmd, env=wrapper_env)

    build_rt_cmd = [
        sys.executable,
        this_dir / "scripts/build-rt-builtins.py",
        "--build-dir", build / "compiler-rt-builtins",
        "--sysroot", sysroot,
        "--llvm-target", args.llvm_target,
        "--clang", args.clang,
        "--jobs", str(args.jobs),
    ]

    if args.llvm_src is not None:
        build_sysroot_cmd.extend(["--llvm-src", args.llvm_src.resolve()])

    run(build_rt_cmd, env=wrapper_env)

    run(
        [
            sys.executable,
            this_dir / "scripts/install-extra-includes.py",
            "--include-dir", this_dir / "include",
            "--sysroot", sysroot,
        ],
        env=wrapper_env,
    )

    print()
    print("Done.")
    print(f"External toolchain path: {out}")
    print(f"Buildroot prefix:        {args.target}")
    print(f"Sysroot:                 {sysroot}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())