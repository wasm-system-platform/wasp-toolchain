from pathlib import Path
import shutil
import subprocess


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required host tool not found in PATH: {name}")


def run(argv, *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    printable = " ".join(str(x) for x in argv)
    if cwd:
        print(f"+ cd {cwd} && {printable}")
    else:
        print(f"+ {printable}")

    subprocess.run([str(x) for x in argv], cwd=cwd, env=env, check=True)
