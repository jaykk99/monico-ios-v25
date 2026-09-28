# 🍎 Monico iOS

**Monico terminal for iPhone/iPad** — a Python/Toga mobile app with an embedded
local web server (Microdot) serving a tabbed terminal UI (Terminal, Forensics, System).

## Status: v4.2.1 (Briefcase/Toga app)

## What it actually is
- `app.py` — Toga app: opens a `toga.WebView` pointed at a local Microdot server on port 5000.
- `POST /api/execute` — sends a command string to the built-in `MonaCoreV27` engine, which returns a canned status line (there is no external AI model call; it works fully offline and keyless).
- `GET /api/health` — CPU usage via `psutil`; reports `OPTIMAL` under 25% CPU, `THROTTLING` above.
- `health_guard.py` — standalone CPU health checker (`python health_guard.py`).

## Run locally (desktop, for UI testing)
```bash
pip install -r requirements.txt
python app.py        # serves the UI at http://localhost:5000
python health_guard.py
```

## Build for iOS
Requires macOS + Xcode (Briefcase cannot build iOS targets on Linux):
```bash
pip install briefcase
briefcase create ios
briefcase build ios
briefcase run ios
```
A GitHub Actions workflow (`.github/workflows/ios_build.yml`) builds the IPA on `macos-latest` on every push.

## Files
| File | Purpose |
|---|---|
| `app.py` | Toga app + Microdot server + inline terminal UI |
| `health_guard.py` | CPU guard (25% limit on iOS) |
| `resources/ui/index.html` | Standalone copy of the terminal UI |
| `index_production.html` | Alternate production UI variant |
| `monico_diag_report.json` | Last diagnostic snapshot (informational) |

## Notes
- No API keys required; everything runs on-device.
- `toga.WebView` needs a real iOS device/simulator — `python app.py` on desktop opens the native window if Toga supports your platform.
