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


def python_dependencies_satisfied(requirements: Path) -> bool:
    checker = r"""
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from packaging.requirements import Requirement
import sys

for raw in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines():
    line = raw.strip()
    if not line or line.startswith('#') or line.startswith('-r '):
        continue
    requirement = Requirement(line)
    if requirement.marker and not requirement.marker.evaluate():
        continue
    try:
        installed = version(requirement.name)
    except PackageNotFoundError:
        raise SystemExit(1)
    if requirement.specifier and installed not in requirement.specifier:
        raise SystemExit(1)
"""
    result = subprocess.run(
        [str(VENV_PYTHON), "-c", checker, str(requirements)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def node_dependencies_satisfied(npm: str) -> bool:
    result = subprocess.run(
        [npm, "ls", "--depth=0", "--silent"],
        cwd=ROOT / "web",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def ensure_python() -> None:
    requirements = ROOT / "requirements.txt"
    wanted = digest(requirements)
    stamp = STATE_DIR / "python.sha256"
    installed = stamp.read_text().strip() if stamp.exists() else ""

    created = False
    if not VENV_PYTHON.exists():
        print("[setup] Creating Python environment once...")
        run([sys.executable, "-m", "venv", str(ROOT / ".venv")])
        installed = ""
        created = True

    if installed != wanted:
        if not created and not installed and python_dependencies_satisfied(requirements):
            print("[fast] Existing Python environment already satisfies this version.")
        else:
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
        if not installed and next_module.exists() and node_dependencies_satisfied(npm):
            print("[fast] Existing frontend dependencies already satisfy this version.")
        else:
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
