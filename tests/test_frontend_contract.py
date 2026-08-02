from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_browser_api_defaults_to_same_origin_proxy():
    api_source = (ROOT / "web/lib/api.ts").read_text(encoding="utf-8")
    assert '|| "/backend"' in api_source
    assert 'init?.body !== undefined' in api_source


def test_next_proxy_targets_local_backend():
    config = (ROOT / "web/next.config.ts").read_text(encoding="utf-8")
    assert 'source: "/backend/:path*"' in config
    assert 'http://127.0.0.1:8000' in config


def test_windows_launcher_waits_for_proxied_frontend_health():
    launcher = (ROOT / "start_product_windows.bat").read_text(encoding="utf-8")
    assert "http://localhost:3000/backend/health" in launcher
    assert "set NEXT_PUBLIC_API_URL=" in launcher
    assert "BACKEND_INTERNAL_URL=http://127.0.0.1:8000" in launcher
