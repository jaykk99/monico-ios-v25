"""Monico iOS v4.3.0 - on-device terminal app.

Toga app that serves a local Microdot web server (bound to 127.0.0.1 only)
and displays the terminal UI in a toga.WebView pointed at it.

Everything runs on-device: no API keys, no cloud calls, no network access
required. The web UI is served from resources/ui/app_ui.html (fully
offline, zero CDN dependencies) so it also works in the iOS WebView
without internet.
"""

import os
import platform
import threading
from datetime import datetime

try:
    import psutil
except ImportError:  # iOS wheels don't exist for psutil; degrade gracefully
    psutil = None

from microdot import Microdot, Response

try:
    import toga
    from toga.style import Pack
except Exception:  # dev machines without a Toga GUI backend
    toga = None
    Pack = None

APP_NAME = "Monico"
APP_VERSION = "4.3.0"
HOST = "127.0.0.1"  # never expose the local engine on the LAN
PORT = 5000
MAX_CMD_LEN = 500
CPU_LIMIT = 25.0  # iOS thermal guard
BOOT_TIME = datetime.now()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_PATH = os.path.join(BASE_DIR, "resources", "ui", "app_ui.html")
PREVIEW_PATH = os.path.join(BASE_DIR, "resources", "ui", "preview.html")


# ---------------------------------------------------------------- engine

class MonaCore:
    """On-device directive engine (keyless, offline)."""

    def __init__(self):
        self.identity = f"MONICO iOS V{APP_VERSION}"

    def execute(self, text):
        text = (text or "").strip()
        if not text:
            return "ERR: empty directive."
        if len(text) > MAX_CMD_LEN:
            return f"ERR: directive too long ({len(text)} > {MAX_CMD_LEN})."
        low = text.lower()
        if low == "help":
            return ("COMMANDS: help | health | sysinfo | about | clear\n"
                    "Type anything else to run a directive through the "
                    "on-device engine.")
        if low == "health":
            h = health_snapshot()
            if h["cpu"] is None:
                return f"HEALTH: {h['status']} (psutil unavailable on iOS)"
            return (f"HEALTH: {h['status']} - CPU {h['cpu']}% / "
                    f"MEM {h['memory']}%")
        if low == "sysinfo":
            s = system_snapshot()
            if s["cpu_count"] is None:
                return (f"SYS: {s['platform']} {s['arch']} | "
                        "hardware stats unavailable on iOS")
            return (f"SYS: {s['platform']} {s['arch']} | CPUs {s['cpu_count']} "
                    f"| RAM {s['mem_total_gb']} GB | Disk {s['disk_total_gb']} GB")
        if low == "about":
            return (f"{self.identity} - on-device terminal. "
                    "No cloud, no keys, no network.")
        return f"[ENGINE] {self.identity}: Directive '{text}' executed."


# ------------------------------------------------------------ snapshots

def health_snapshot():
    if psutil is None:
        return {"cpu": None, "memory": None, "status": "UNAVAILABLE",
                "cpu_limit": CPU_LIMIT}
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory().percent
    status = "OPTIMAL" if cpu < CPU_LIMIT else "THROTTLING"
    return {"cpu": round(cpu, 1), "memory": round(mem, 1), "status": status,
            "cpu_limit": CPU_LIMIT}


def system_snapshot():
    if psutil is None:
        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "arch": platform.machine(),
            "cpu_count": None,
            "cpu_physical": None,
            "mem_total_gb": None,
            "mem_used_gb": None,
            "disk_total_gb": None,
            "disk_used_gb": None,
            "disk_free_gb": None,
            "python": platform.python_version(),
            "uptime_s": int((datetime.now() - BOOT_TIME).total_seconds()),
            "boot_time": None,
        }
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    uptime = (datetime.now() - BOOT_TIME).total_seconds()
    return {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "arch": platform.machine(),
        "cpu_count": psutil.cpu_count(logical=True),
        "cpu_physical": psutil.cpu_count(logical=False),
        "mem_total_gb": round(vm.total / 1e9, 1),
        "mem_used_gb": round(vm.used / 1e9, 1),
        "disk_total_gb": round(disk.total / 1e9, 1),
        "disk_used_gb": round(disk.used / 1e9, 1),
        "disk_free_gb": round(disk.free / 1e9, 1),
        "python": platform.python_version(),
        "uptime_s": int(uptime),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
    }


def forensics_snapshot(top_n=8):
    """Real on-device forensic scan via psutil (no network, no keys).

    Returns a degraded payload when psutil is unavailable (iOS).
    """
    if psutil is None:
        return {
            "scanned_at": datetime.now().isoformat(timespec="seconds"),
            "process_count": 0,
            "top_processes": [],
            "network_connections": -1,
            "disk_used_gb": None,
            "disk_total_gb": None,
            "unavailable": "psutil has no iOS wheels; scan disabled on device",
        }
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = p.info
            info["cpu_percent"] = round(info.get("cpu_percent") or 0.0, 1)
            info["memory_percent"] = round(info.get("memory_percent") or 0.0, 2)
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x["cpu_percent"], reverse=True)
    try:
        conns = len(psutil.net_connections(kind="inet"))
    except (psutil.AccessDenied, psutil.Error):
        conns = -1  # restricted on this platform
    disk = psutil.disk_usage("/")
    return {
        "scanned_at": datetime.now().isoformat(timespec="seconds"),
        "process_count": len(procs),
        "top_processes": procs[:top_n],
        "network_connections": conns,
        "disk_used_gb": round(disk.used / 1e9, 1),
        "disk_total_gb": round(disk.total / 1e9, 1),
    }


# ---------------------------------------------------------------- server

engine = MonaCore()
server = Microdot()


@server.route("/api/execute", methods=["POST"])
def api_execute(req):
    try:
        body = req.json or {}
    except Exception:
        body = {}
    return {"output": engine.execute(body.get("command", ""))}


@server.route("/api/health")
def api_health(req):
    return health_snapshot()


@server.route("/api/system")
def api_system(req):
    return system_snapshot()


@server.route("/api/forensics")
def api_forensics(req):
    return forensics_snapshot()


def _serve_file(path, fallback_title):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            html = fh.read()
    except OSError:
        html = (f"<html><body><h1>{fallback_title}</h1>"
                "<p>UI asset missing.</p></body></html>")
    return Response(html, headers={"Content-Type": "text/html; charset=utf-8"})


@server.route("/")
def ui(req):
    return _serve_file(UI_PATH, APP_NAME)


@server.route("/preview")
def preview(req):
    """Polished desktop showcase: the app running live inside a phone frame."""
    return _serve_file(PREVIEW_PATH, f"{APP_NAME} preview")


# ------------------------------------------------------------------- app

if toga is not None:
    class MonicoApp(toga.App):
        def startup(self):
            self.main_window = toga.MainWindow(title=APP_NAME)
            threading.Thread(
                target=lambda: server.run(host=HOST, port=PORT),
                daemon=True,
            ).start()
            self.web_view = toga.WebView(
                url=f"http://{HOST}:{PORT}/", style=Pack(flex=1)
            )
            self.main_window.content = self.web_view
            self.main_window.show()
else:
    MonicoApp = None


def main():
    if toga is None:
        # Desktop/dev fallback: no GUI backend, just serve the web UI.
        print(f"[{APP_NAME}] Toga GUI backend not installed; "
              f"serving web UI at http://{HOST}:{PORT}/")
        server.run(host=HOST, port=PORT)
        return None
    return MonicoApp(APP_NAME, "com.jaykk99.monico")


if __name__ == "__main__":
    app = main()
    if app is not None:
        app.main_loop()
