"""Mac CI: テストを1件ずつ子プロセスで回し、落ちた件名を注釈に出す。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _annotate(file: str, message: str) -> None:
    safe = message.replace("%", "%25").replace("\r", " ").replace("\n", "%0A")
    print(f"::error file={file}::{safe}", flush=True)


def _collect(path: Path) -> list[str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        _annotate(
            str(path.relative_to(ROOT)),
            f"collect failed {proc.returncode}\n{proc.stdout}\n{proc.stderr}",
        )
        sys.exit(1)
    nodes: list[str] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if "::" in line and not line.startswith("="):
            nodes.append(line)
    return nodes


def main() -> int:
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        for node in _collect(path):
            print(f"RUN {node}", flush=True)
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "--tb=short", node],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            if proc.returncode == 0:
                continue
            detail = (proc.stdout or "") + (proc.stderr or "")
            _annotate(
                str(path.relative_to(ROOT)),
                f"{node} exit {proc.returncode}\n{detail[-1200:]}",
            )
            print(detail, flush=True)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
