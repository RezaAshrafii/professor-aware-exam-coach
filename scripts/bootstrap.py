from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".dependency_state"
VENV_PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def digest(*paths: Path) -> str:
    value = hashlib.sha256()
    for path in paths:
        value.update(path.name.encode())
        if path.exists():
            value.update(path.read_bytes())
    return value.hexdigest()


def node_dependency_digest(package: Path, lock: Path) -> str:
    """Ignore app-version-only edits; reinstall only when dependency data changes."""

    value = hashlib.sha256()
    package_data = json.loads(package.read_text(encoding="utf-8"))
    dependency_data = {
        key: package_data.get(key, {})
        for key in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies", "engines")
    }
    value.update(json.dumps(dependency_data, sort_keys=True).encode())
    if lock.exists():
        lock_data = json.loads(lock.read_text(encoding="utf-8"))
        lock_data.pop("name", None)
        lock_data.pop("version", None)
        root = (lock_data.get("packages") or {}).get("")
        if isinstance(root, dict):
            root.pop("name", None)
            root.pop("version", None)
        value.update(json.dumps(lock_data, sort_keys=True).encode())
    return value.hexdigest()


def run(command: list[str], *, cwd: Path = ROOT) -> None:
    print("$", " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def ensure_python() -> None:
    requirements = ROOT / "requirements.txt"
    wanted = digest(requirements)
    stamp = STATE_DIR / "python.sha256"
    installed = stamp.read_text().strip() if stamp.exists() else ""

    if not VENV_PYTHON.exists():
        print("[setup] Creating Python environment once...")
        run([sys.executable, "-m", "venv", str(ROOT / ".venv")])
        installed = ""

    if installed != wanted:
        print("[setup] Python dependencies changed; installing only this time...")
        run([str(VENV_PYTHON), "-m", "pip", "install", "-r", str(requirements)])
        STATE_DIR.mkdir(exist_ok=True)
        stamp.write_text(wanted)
    else:
        print("[fast] Python dependencies are already ready.")


def ensure_node() -> None:
    npm = shutil.which("npm")
    if npm is None:
        raise RuntimeError("Node.js/npm is not installed.")
    package = ROOT / "web" / "package.json"
    lock = ROOT / "web" / "package-lock.json"
    wanted = node_dependency_digest(package, lock)
    stamp = STATE_DIR / "node.sha256"
    installed = stamp.read_text().strip() if stamp.exists() else ""
    next_module = ROOT / "web" / "node_modules" / "next"

    if installed != wanted or not next_module.exists():
        print("[setup] Frontend dependencies changed; installing only this time...")
        command = [npm, "ci", "--no-audit", "--no-fund"] if lock.exists() else [npm, "install", "--no-audit", "--no-fund"]
        run(command, cwd=ROOT / "web")
        # npm install may create package-lock.json; stamp the final state.
        STATE_DIR.mkdir(exist_ok=True)
        stamp.write_text(node_dependency_digest(package, lock))
    else:
        print("[fast] Frontend dependencies are already ready.")


def main() -> int:
    ensure_python()
    ensure_node()
    for source, target in [
        (ROOT / ".env.example", ROOT / ".env"),
        (ROOT / "web" / ".env.local.example", ROOT / "web" / ".env.local"),
    ]:
        if source.exists() and not target.exists():
            shutil.copyfile(source, target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
