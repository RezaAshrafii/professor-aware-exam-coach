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
