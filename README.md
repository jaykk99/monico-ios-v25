# 🍎 Monico iOS

**Monico terminal for iPhone/iPad** — a Python/Toga mobile app with an embedded
local web server (Microdot) serving a tabbed terminal UI (Terminal, Forensics, System).

## Status: v4.4.0 (Briefcase/Toga app)

## What it actually is
- `src/monicoios/app.py` — Toga app: opens a `toga.WebView` pointed at a local
  Microdot server bound to **127.0.0.1:5000** (never exposed on the LAN).
- `POST /api/execute` — sends a command string to the on-device `MonaCore`
  engine. Real commands: `help`, `health`, `sysinfo`, `about`, `uptime`,
  `date`, `echo <text>`, `cpu`, `disk`, `ps [n]`. Unknown commands return
  an honest `ERR` (the engine never fakes output). Input is length-capped
  (500 chars) and all output is HTML-escaped in the UI.
  No external AI model call; works fully offline and keyless.
- `GET /api/health` — CPU/memory via `psutil`; `OPTIMAL` under 25% CPU,
  `THROTTLING` above (iOS thermal guard).
- `GET /api/system` — real device info: platform, arch, CPU counts, RAM,
  disk, Python version, uptime.
- `GET /api/forensics` — real on-device scan: process table ranked by CPU,
  network connection count, disk usage.
- `/` — the app UI (`src/monicoios/resources/ui/app_ui.html`): iOS-style
  terminal with command history, forensic scanner, and live system gauges.
  **Zero CDN dependencies** — renders fully offline inside the iOS WebView.
- `/preview` — desktop showcase page: the live app inside a phone frame,
  feature cards, and build instructions.
- `health_guard.py` — standalone CPU health checker (`python health_guard.py`).

## Run locally (desktop, for UI testing)
```bash
pip install -r requirements.txt
python app.py        # serves the UI at http://127.0.0.1:5000
python health_guard.py
pytest tests/ -q     # 20 tests: API routes, UI assets, health guard
```

Open http://127.0.0.1:5000/preview for the polished showcase.

## Build for iOS
Requires macOS + Xcode (Briefcase cannot build iOS targets on Linux):

```bash
pip install briefcase
briefcase create ios
briefcase build ios
briefcase run ios
```
The package layout is Briefcase-standard: sources live in
`src/monicoios/` with `src/monicoios/__main__.py` as the entry point (the iOS
bootstrap runs the `MainModule` as `__main__`), so `briefcase create`
packages the Python code **and** the `resources/ui/` HTML assets into the
app bundle (verified via a Linux `briefcase create` packaging run).

A GitHub Actions workflow (`.github/workflows/ios_build.yml`) builds the IPA
on `macos-latest` on every push and uploads it as the `Monico-iOS-IPA`
artifact — grab the latest from the repo's Actions tab.
**macOS + Xcode + an Apple Developer account are required** to install the
built IPA on a physical iPhone/iPad (or run it in the Xcode simulator);
ad-hoc distribution or TestFlight handles signing.

## Files
| File | Purpose |
|---|---|
| `app.py` | Desktop/dev entry point (imports `monicoios.app`) |
| `src/monicoios/app.py` | Toga app + Microdot server + API routes |
| `src/monicoios/resources/ui/app_ui.html` | Canonical app UI (served at `/`) |
| `src/monicoios/resources/ui/preview.html` | Desktop showcase (served at `/preview`) |
| `src/monicoios/resources/ui/index.html` | Standalone copy of the app UI |
| `health_guard.py` | CPU guard (25% limit on iOS) |
| `tests/test_app.py` | Pytest suite (14 tests) |
| `monico_diag_report.json` | Last diagnostic snapshot (informational) |

## Notes
- No API keys required; everything runs on-device.
- `psutil` ships no iOS wheels, so it is a desktop-only dependency: on iOS
  the health/forensics endpoints degrade gracefully (`UNAVAILABLE`) instead
  of crashing. Desktop and CI tests run with psutil installed.
- No Swift/SwiftUI in this repo: the "native" app is Python via
  BeeWare Toga/Briefcase, rendered in a `WebView`. It cannot be compiled
  or run on iOS without macOS + Xcode (or the CI-built IPA).
- `toga.WebView` needs a real iOS device/simulator — `python app.py` on a
  desktop without a Toga GUI backend serves the web UI directly instead.
