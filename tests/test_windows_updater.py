from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATER = ROOT / "update_from_zip.bat"


def test_one_click_updater_exists_and_preserves_runtime_data() -> None:
    content = UPDATER.read_text(encoding="utf-8")
    assert "Expand-Archive" in content
    assert "start_product_windows.bat" in content
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
        assert protected in content


def test_updater_rejects_dirty_tracked_worktree() -> None:
    content = UPDATER.read_text(encoding="utf-8")
    assert "git status --porcelain --untracked-files=no" in content
    assert "Tracked project files have local changes" in content


def test_updater_accepts_explicit_zip_or_auto_discovers_one() -> None:
    content = UPDATER.read_text(encoding="utf-8")
    assert 'set "ACOS_ZIP=%~1"' in content
    assert "Downloads" in content
    assert "Desktop" in content
    assert "professor_aware_exam_coach" in content
