from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ToolchainConfig:
    out: Path
    build: Path
    target: str
    llvm_target: str
    musl_src: Path
    llvm_src: Path
    clang: str
    clangxx: str
    version: str
    jobs: int
    enable_cxx: bool

    @property
    def bindir(self) -> Path:
        return self.out / "bin"

    @property
    def sysroot(self) -> Path:
        return self.out / self.target / "sysroot"

    @property
    def libdir(self) -> Path:
        return self.sysroot / "usr/lib"

    @property
    def includedir(self) -> Path:
        return self.sysroot / "usr/include"
