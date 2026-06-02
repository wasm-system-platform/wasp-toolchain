#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.process import run


LLVM_REPO = "https://github.com/llvm/llvm-project.git"
DEFAULT_LLVM_REF = "llvmorg-20.1.8"


def ensure_llvm_src(
    *,
    llvm_src: Path | None,
    llvm_ref: str,
    download_dir: Path
) -> Path:
    if llvm_src is not None:
        llvm_src = musl_src.resolve()
        if not (llvm_src / "compiler-rt").exists():
            raise RuntimeError(f"llvm source does not look valid: {llvm_src}")
        return llvm_src

    download_dir.parent.mkdir(parents=True, exist_ok=True)
    dst = download_dir / "llvm-project"

    if not dst.exists():
        run(
            [
                "git",
                "clone",
                "--depth", "1",
                "--branch", llvm_ref,
                LLVM_REPO,
                dst,
            ]
        )

    compiler_rt_src = dst / "compiler-rt"
    if not compiler_rt_src.exists():
        raise RuntimeError(f"compiler-rt/ not found after cloning {LLVM_REPO}@{ref}")

    return dst.resolve()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--llvm-src", type=Path)
    parser.add_argument("--llvm-ref", default=DEFAULT_LLVM_REF)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--sysroot", type=Path, required=True)
    parser.add_argument("--llvm-target", required=True)
    parser.add_argument("--clang", default="clang")
    parser.add_argument("--jobs", type=int, required=True)
    args = parser.parse_args()

    llvm_src = ensure_llvm_src(
        llvm_src=args.llvm_src, 
        llvm_ref=args.llvm_ref,
        download_dir=args.build_dir.parent / "sources",
    )
    compiler_rt_src = llvm_src / "compiler-rt"

    if args.build_dir.exists():
        shutil.rmtree(args.build_dir)

    args.build_dir.mkdir(parents=True)

    run(
        [
            "cmake",
            "-G", "Ninja",
            str(compiler_rt_src),
            "-DCMAKE_BUILD_TYPE=Release",
            "-DCMAKE_SYSTEM_NAME=Generic",
            "-DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY",
            f"-DCMAKE_SYSROOT={args.sysroot}",
            f"-DCMAKE_C_COMPILER={args.clang}",
            f"-DCMAKE_ASM_COMPILER={args.clang}",
            f"-DCMAKE_C_COMPILER_TARGET={args.llvm_target}",
            f"-DCMAKE_ASM_COMPILER_TARGET={args.llvm_target}",
            "-DCOMPILER_RT_BUILD_BUILTINS=ON",
            "-DCOMPILER_RT_DEFAULT_TARGET_ONLY=ON",
            "-DCOMPILER_RT_BAREMETAL_BUILD=ON",
            "-DCOMPILER_RT_BUILD_SANITIZERS=OFF",
            "-DCOMPILER_RT_BUILD_XRAY=OFF",
            "-DCOMPILER_RT_BUILD_LIBFUZZER=OFF",
            "-DCOMPILER_RT_BUILD_PROFILE=OFF",
            "-DCOMPILER_RT_BUILD_MEMPROF=OFF",
            "-DCOMPILER_RT_BUILD_CRT=OFF",
            "-DCOMPILER_RT_BUILD_ORC=OFF",
        ],
        cwd=args.build_dir,
    )

    run(["ninja", f"-j{args.jobs}"], cwd=args.build_dir)

    candidates = sorted(args.build_dir.rglob("libclang_rt.builtins*.a"))
    if not candidates:
        raise RuntimeError("compiler-rt builtins archive not found")

    dst = args.sysroot / "usr/lib/libclang_rt.builtins-wasm32.a"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(candidates[0], dst)

    libgcc = args.sysroot / "usr/lib/libgcc.a"
    if libgcc.exists() or libgcc.is_symlink():
        libgcc.unlink()

    libgcc.symlink_to(dst.name)

    print(dst)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())