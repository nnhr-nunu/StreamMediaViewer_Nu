"""Mac CI: macOS 12 で動く wheel だけ入れてからインストールする。"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WHEELHOUSE = Path.home() / "macos12-wheels"


def _platforms() -> list[str]:
    arch = subprocess.check_output(["uname", "-m"], text=True).strip()
    plats = ["macosx_12_0_universal2"]
    if arch == "x86_64":
        plats.append("macosx_12_0_x86_64")
    else:
        plats.append("macosx_12_0_arm64")
    return plats


def _requirements_from_pyproject() -> list[str]:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    reqs: list[str] = []
    collecting = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("dependencies") or stripped.startswith("dev ="):
            collecting = True
            continue
        if collecting and stripped.startswith("]"):
            collecting = False
            continue
        if not collecting:
            continue
        match = re.search(r'"([^"]+)"', stripped)
        if match is None:
            continue
        req = match.group(1)
        if "sys_platform != 'darwin'" in req:
            continue
        reqs.append(req.split(";")[0].strip())
    reqs.extend(["numpy", "setuptools", "wheel"])
    return reqs


def _run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    WHEELHOUSE.mkdir(parents=True, exist_ok=True)
    plat_args: list[str] = []
    for plat in _platforms():
        plat_args.extend(["--platform", plat])
    _run(
        [
            sys.executable,
            "-m",
            "pip",
            "download",
            "-d",
            str(WHEELHOUSE),
            "--python-version",
            "310",
            *plat_args,
            "--only-binary=:all:",
            *_requirements_from_pyproject(),
        ]
    )
    _run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-index",
            "--find-links",
            str(WHEELHOUSE),
            "setuptools",
            "wheel",
        ]
    )
    _run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-index",
            "--find-links",
            str(WHEELHOUSE),
            "-e",
            f"{ROOT}[dev]",
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
