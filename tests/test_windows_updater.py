from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAT = ROOT / "UPDATE_ACOS.bat"
SCRIPT = ROOT / "ACOS_Update.ps1"
COMPATIBILITY_WRAPPER = ROOT / "update_from_zip.bat"


def test_one_click_updater_exists_and_preserves_runtime_data() -> None:
    bat = BAT.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")
    assert "ACOS_Update.ps1" in bat
    assert "Expand-Archive" in script
    assert "start_product_windows.bat" in COMPATIBILITY_WRAPPER.read_text(encoding="utf-8")
    for protected in (
        ".git",
        ".venv",
        ".dependency_state",
        "data",
        "node_modules",
        ".next",
        ".env",
        ".env.local",
    ):
        assert protected in script


def test_updater_rejects_dirty_tracked_worktree() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "git status --porcelain --untracked-files=no" in content
    assert "Commit or restore tracked changes before updating" in content


def test_updater_accepts_explicit_zip_or_auto_discovers_one() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert '[string]$ZipPath = ""' in content
    assert "Downloads" in content
    assert "Desktop" in content
    assert "professor_aware_exam_coach" in content


def test_updater_does_not_reinstall_unchanged_dependencies() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "Python dependencies unchanged; skipped." in content
    assert "Frontend dependencies unchanged; skipped." in content
    assert "Get-HashOrEmpty" in content
    assert "$oldPackageLockHash" in content


def test_old_updater_name_remains_as_a_compatibility_wrapper() -> None:
    content = COMPATIBILITY_WRAPPER.read_text(encoding="utf-8")
    assert "ACOS_Update.ps1" not in content
    assert "start_product_windows.bat" in content
