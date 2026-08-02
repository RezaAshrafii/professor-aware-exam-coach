from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*command: str) -> None:
    print(f"\n$ {' '.join(command)}")
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    run(sys.executable, "-m", "compileall", "-q", "app", "tests")
    run(sys.executable, "-m", "ruff", "check", "--select", "E9,F", ".")
    run(sys.executable, "-m", "pytest")
    run("node", "scripts/check_frontend_syntax.mjs")
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
