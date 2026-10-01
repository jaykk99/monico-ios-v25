"""Pytest suite for the Monico iOS app server (app.py) and health_guard.

Runs against the real Microdot app with a stubbed `toga` module (no GUI
backend needed on CI/Linux). Exercises real psutil-backed endpoints.
"""
import asyncio
import os
import sys
import types

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _stub_toga():
    toga = types.ModuleType("toga")
    style = types.ModuleType("toga.style")

    class Pack(dict):
        def __init__(self, **k):
            super().__init__(**k)

    style.Pack = Pack

    class App:
        def __init__(self, *a, **k):
            pass

    class MainWindow:
        def __init__(self, *a, **k):
            self.content = None

        def show(self):
            pass

    class WebView:
        def __init__(self, *a, **k):
            self.url = k.get("url")

    toga.App, toga.MainWindow, toga.WebView = App, MainWindow, WebView
    sys.modules["toga"] = toga
    sys.modules["toga.style"] = style


_stub_toga()
sys.path.insert(0, os.path.join(REPO, "src"))

from monicoios import app  # noqa: E402
from microdot.test_client import TestClient  # noqa: E402
from health_guard import HealthGuard  # noqa: E402


@pytest.fixture()
def client():
    return TestClient(app.server)


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_execute_directive(client):
    r = _run(client.post("/api/execute", body='{"command":"status"}',
                         headers={"Content-Type": "application/json"}))
    assert r.status_code == 200
    # honest engine: unknown commands are errors, never faked output
    assert r.json["output"].startswith("ERR: unknown command")


def _post(client, command):
    return _run(client.post("/api/execute", body='{"command":"%s"}' % command,
                            headers={"Content-Type": "application/json"}))


def test_new_commands_real_output(client):
    r = _post(client, "uptime")
    assert r.json["output"].startswith("UPTIME: ")
    assert "h " in r.json["output"] and "m " in r.json["output"]
    r = _post(client, "date")
    assert r.json["output"].startswith("DATE: 20")
    r = _post(client, "echo hello monico")
    assert r.json["output"] == "hello monico"
    r = _post(client, "echo")
    assert r.json["output"].startswith("ERR: echo needs text")
    r = _post(client, "cpu")
    assert r.json["output"].startswith("CPU: ")
    assert "%" in r.json["output"]
    r = _post(client, "disk")
    assert r.json["output"].startswith("DISK: ")
    assert "GB" in r.json["output"]
    r = _post(client, "ps 3")
    out = r.json["output"]
    assert out.startswith("PROCS: ")
    assert len(out.splitlines()) == 4  # header + 3 rows
    r = _post(client, "ps banana")
    assert "usage" in r.json["output"].lower()
    r = _post(client, "HELP")  # case-insensitive
    assert "COMMANDS" in r.json["output"]


def test_unknown_command_is_honest_error(client):
    r = _post(client, "frobnicate-the-thing")
    assert r.status_code == 200
    assert r.json["output"].startswith("ERR: unknown command")


def test_new_commands_degraded_on_ios(client, monkeypatch):
    """ps/cpu/disk must degrade gracefully without psutil (iOS)."""
    monkeypatch.setattr(app, "psutil", None)
    assert "UNAVAILABLE" in app.engine.execute("cpu")
    assert "UNAVAILABLE" in app.engine.execute("disk")
    assert "ios wheels" in app.engine.execute("ps").lower()
    # pure-python commands still work on iOS
    assert app.engine.execute("uptime").startswith("UPTIME: ")
    assert app.engine.execute("echo x") == "x"
    assert app.engine.execute("date").startswith("DATE: ")


def test_version_consistent_everywhere():
    """VERSION, package, and app server must agree on the release."""
    with open(os.path.join(REPO, "VERSION")) as fh:
        v = fh.read().strip()
    import monicoios
    assert monicoios.__version__ == v
    assert app.APP_VERSION == v


def test_execute_help_command(client):
    r = _run(client.post("/api/execute", body='{"command":"help"}',
                         headers={"Content-Type": "application/json"}))
    assert "COMMANDS" in r.json["output"]


def test_execute_health_command(client):
    r = _run(client.post("/api/execute", body='{"command":"health"}',
                         headers={"Content-Type": "application/json"}))
    assert "HEALTH:" in r.json["output"]
    assert "CPU" in r.json["output"]


def test_execute_sysinfo_command(client):
    r = _run(client.post("/api/execute", body='{"command":"sysinfo"}',
                         headers={"Content-Type": "application/json"}))
    assert "SYS:" in r.json["output"]


def test_execute_empty_and_oversized(client):
    r = _run(client.post("/api/execute", body="{}",
                         headers={"Content-Type": "application/json"}))
    assert r.json["output"].startswith("ERR:")
    big = "x" * (app.MAX_CMD_LEN + 1)
    r = _run(client.post("/api/execute", body='{"command":"%s"}' % big,
                         headers={"Content-Type": "application/json"}))
    assert "too long" in r.json["output"]


def test_execute_malformed_body(client):
    r = _run(client.post("/api/execute", body="not-json{{{",
                         headers={"Content-Type": "application/json"}))
    assert r.status_code == 200
    assert r.json["output"].startswith("ERR:")


def test_health_endpoint(client):
    r = _run(client.get("/api/health"))
    assert r.status_code == 200
    data = r.json
    assert data["status"] in ("OPTIMAL", "THROTTLING")
    assert isinstance(data["cpu"], (int, float))
    assert isinstance(data["memory"], (int, float))
    assert data["cpu_limit"] == app.CPU_LIMIT


def test_system_endpoint_real_values(client):
    import platform as _plat
    r = _run(client.get("/api/system"))
    assert r.status_code == 200
    data = r.json
    assert data["platform"] == _plat.system()
    assert data["arch"] == _plat.machine()
    assert data["cpu_count"] and data["cpu_count"] > 0
    assert data["mem_total_gb"] > 0
    assert data["disk_total_gb"] > 0
    assert data["python"] == _plat.python_version()


def test_forensics_endpoint_real_scan(client):
    r = _run(client.get("/api/forensics"))
    assert r.status_code == 200
    data = r.json
    assert data["process_count"] > 0
    assert len(data["top_processes"]) > 0
    first = data["top_processes"][0]
    assert "pid" in first and "name" in first and "cpu_percent" in first
    assert isinstance(data["network_connections"], int)
    assert data["disk_total_gb"] > 0


def test_ui_served_offline_first(client):
    r = _run(client.get("/"))
    assert r.status_code == 200
    assert "text/html" in r.headers.get("Content-Type", "")
    html = r.text
    # all three tabs present
    assert "tab-terminal" in html and "tab-forensics" in html
    assert "tab-system" in html
    # offline-first: no external CDN/scripts
    assert "cdn.tailwindcss.com" not in html
    assert "https://" not in html.replace("http://127.0.0.1", "")


def test_ui_is_canonical_file(client):
    with open(app.UI_PATH, encoding="utf-8") as fh:
        on_disk = fh.read()
    r = _run(client.get("/"))
    assert r.text == on_disk


def test_preview_page(client):
    r = _run(client.get("/preview"))
    assert r.status_code == 200
    html = r.text
    assert "<iframe" in html and 'src="/"' in html
    assert "MONICO" in html


def test_health_guard():
    g = HealthGuard()
    res = g.check()
    assert res["status"] in ("OPTIMAL", "THROTTLING")
    assert res["cpu"].endswith("%")


def test_server_bound_to_localhost():
    assert app.HOST == "127.0.0.1"
    assert app.PORT == 5000


def test_briefcase_main_module_resolves():
    """The iOS backend calls app.main_module(); it must stay a method
    returning the module name run as __main__ by the iOS bootstrap."""
    from briefcase.config import AppConfig
    cfg = AppConfig(
        app_name="monicoios",
        formal_name="Monico",
        version="4.4.0",
        bundle="com.jaykk99.monicoios",
        description="test",
        sources=["src/monicoios"],
        test_mode=False,
    )
    assert cfg.main_module() == "monicoios"
    assert callable(AppConfig.main_module)
    # and the module run as __main__ exists with a startable entry
    import monicoios.__main__  # noqa: F401


def test_degraded_mode_without_psutil(monkeypatch):
    """Simulates iOS where psutil has no wheels: endpoints must not 500."""
    monkeypatch.setattr(app, "psutil", None)
    assert app.health_snapshot()["status"] == "UNAVAILABLE"
    assert app.health_snapshot()["cpu"] is None
    s = app.system_snapshot()
    assert s["cpu_count"] is None and s["platform"]
    f = app.forensics_snapshot()
    assert f["process_count"] == 0 and "unavailable" in f
    assert "unavailable" in app.engine.execute("health").lower() or \
        "UNAVAILABLE" in app.engine.execute("health")
    assert "unavailable" in app.engine.execute("sysinfo").lower()
