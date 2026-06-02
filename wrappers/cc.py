#!/usr/bin/env python3
from pathlib import Path
import os
import sys


TARGET = os.environ.get("WASP_TOOLCHAIN_TARGET", "wasm32-wasp-linux")
LLVM_TARGET = os.environ.get("WASP_LLVM_TARGET", "wasm32-unknown-unknown")
CLANG = os.environ.get("HOST_CLANG", "clang")
VERSION = os.environ.get("GCC_VERSION", "15.0.0")

UNSUPPORTED_FLAGS = [
    "-falign-labels",
    "-falign-jumps",

    "-finline-limit",

    "-fira-region",
    "-fira-hoist-pressure",

    "-freorder-blocks-algorithm",

    "-fno-align-jumps",
    "-fno-align-loops",
    "-fno-align-labels",
    "-fno-prefetch-loop-arrays",
    "-fno-tree-ch",
    "-fno-tree-loop-distribute-patterns",

    "-pie",
    "-static-libgcc",

    "-ztext",

    "-Werror=discarded-array-qualifiers",
    "-Werror=discarded-qualifiers",

    "-Wl,--start-group",
    "-Wl,--end-group",
    "-Wl,-z,now",
    "-Wl,-z,relro",
    "-Wl,--warn-common",
]

OPTIONS_WITH_VALUE = {
    "-o",
    "-I",
    "-isystem",
    "-include",
    "-D",
    "-U",
    "-L",
    "-l",
    "-B",
    "-target",
    "--target",
    "--sysroot",
    "-resource-dir",
    "--resource-dir",
    "-x",
}


def filter_args(args: list[str]) -> list[str]:
    return [
        arg
        for arg in args
        if not any(arg.startswith(flag) for flag in UNSUPPORTED_FLAGS)
    ]


def is_compile_only(args: list[str]) -> bool:
    return any(arg in {"-c", "-S", "-E", "-M", "-MM"} for arg in args)


def has_input_file(args: list[str]) -> bool:
    skip_next = False

    for arg in args:
        if skip_next:
            skip_next = False
            continue

        if arg in OPTIONS_WITH_VALUE:
            skip_next = True
            continue

        if any(arg.startswith(option) for option in OPTIONS_WITH_VALUE):
            continue

        if arg.startswith("-"):
            continue

        return True

    return False


def run_clang_info(
    *,
    clang: str,
    llvm_target: str,
    sysroot: Path,
    resource_dir: Path | None,
    args: list[str],
) -> None:
    cmd = [
        clang,
        f"--target={llvm_target}",
        f"--sysroot={sysroot}",
        f"-resource-dir={resource_dir}",
    ]

    if args == ["-v"]:
        cmd.extend(["-v", "-E", "-x", "c", os.devnull])
    else:
        cmd.extend(args)

    os.execvp(cmd[0], cmd)


def main() -> int:
    toolchain_dir = Path(__file__).resolve().parent.parent
    sysroot = toolchain_dir / TARGET / "sysroot"
    includedir = sysroot / "usr/include"
    libdir = sysroot / "usr/lib"
    resource_dir = sysroot / "usr"

    raw_args = sys.argv[1:]

    # GCC-kompatible Abfragen, die Buildroot gerne nutzt.
    if raw_args == ["-dumpmachine"]:
        print(TARGET)
        return 0

    if raw_args == ["-dumpversion"]:
        print(VERSION.split(".")[0])
        return 0

    if raw_args == ["-dumpfullversion"]:
        print(VERSION)
        return 0

    if raw_args == ["-print-sysroot"]:
        print(sysroot)
        return 0

    if raw_args == ["-print-file-name=libc.a"]:
        print(libdir / "libc.a")
        return 0

    if raw_args in (["-print-libgcc-file-name"], ["-print-file-name=libgcc.a"]):
        print(libdir / "libgcc.a")
        return 0

    if raw_args in (
        ["-v"],
        ["--version"],
        ["-print-search-dirs"],
        ["-print-multi-lib"],
        ["-print-multi-directory"],
        ["-print-resource-dir"],
    ):
        run_clang_info(
            clang=CLANG,
            llvm_target=LLVM_TARGET,
            sysroot=sysroot,
            resource_dir=resource_dir,
            args=raw_args,
        )

    compile_only = is_compile_only(raw_args) or not has_input_file(raw_args)
    args = filter_args(raw_args)

    cmd = [
        CLANG,
        f"--target={LLVM_TARGET}",
        f"--sysroot={sysroot}",
        f"-isystem{includedir}",
        f"-resource-dir={resource_dir}",
        "-D__linux__",
        *args,
    ]

    if not compile_only:
        cmd.extend(
            [
                "-fuse-ld=lld",
                f"-B{libdir}",
                f"-L{libdir}",
                "-Wl,--import-memory",
                "-Wl,-z,stack-size=16777216",
            ]
        )

    os.execvp(cmd[0], cmd)


if __name__ == "__main__":
    raise SystemExit(main())