# Monico iOS v2.5

A production-ready iOS application built with Python and Toga, featuring the **Mythos Bridge** communication layer and an advanced **multi-mode Terminal** for real-time code execution on-device.

---

## Features

### Mythos Bridge
The Mythos Bridge is the core communication layer that connects the WebView-based frontend UI to the native Python backend. It enables seamless, low-latency message passing between the HTML/JavaScript interface and the Toga application through dedicated endpoints:

- `/execute` — Direct code execution via the Terminal mode
- `/chat` — Conversational AI interactions via Chat mode
- `/agent` — Autonomous agent directives via Agent mode

The bridge handles request routing, response streaming, and error recovery (`BRIDGE_ERR` diagnostics), providing a unified interface regardless of the active mode.

### Terminal
The multi-mode Terminal is the primary interface for interacting with Monico. It supports four operational modes accessible via tabbed navigation:

| Mode | Description |
|------|-------------|
| **Chat** | Conversational interface with infinite context and system link |
| **Agent** | Autonomous execution mode for directive-based workflows |
| **Terminal** | Direct code execution with AI auto-language detection |
| **Model** | Model configuration and parameter management |

Key Terminal capabilities:
- **AI Auto-Language Selection** — Automatically detects and routes Python, Shell, and other language payloads
- **OLED Dark Mode** — Pure black (#000000) UI optimized for OLED displays with 15ms TTFT
- **CRT Scanline Overlay** — Retro terminal aesthetic with green phosphor styling
- **Real-time Output Streaming** — Live execution results rendered in a scrollable output pane

### Additional Highlights
- **100Q ARM64 Kernel** — Optimized for Apple Silicon
- **Toga + WebView Architecture** — Native iOS wrapper with a rich HTML/Tailwind CSS frontend
- **CI/CD via GitHub Actions** — Automated builds on push to `main` using Briefcase
- **Briefcase Packaging** — Single-command build and deploy to physical devices and the App Store

---

## Quick Start

### 1. Prepare Production Files

```bash
cp app_production.py app.py
cp index_production.html resources/ui/index.html
cp pyproject_production.toml pyproject.toml
```

### 2. Build and Run on Device

```bash
pip install briefcase
briefcase build ios --device
briefcase run ios --device
```

### 3. Build for Release

```bash
briefcase build ios --release
```

---

## Project Structure

```
monico-ios-v25/
├── app.py                      # Main application (Toga + Mythos Bridge)
├── app_production.py           # Production application source
├── resources/
│   └── ui/
│       └── index.html          # Terminal UI (Chat, Agent, Terminal, Model)
├── index_production.html       # Production UI source
├── pyproject.toml              # Briefcase project config
├── pyproject_production.toml   # Production Briefcase config
├── requirements.txt            # Python dependencies
├── .github/
│   └── workflows/
│       └── build.yml           # CI/CD workflow
├── START_HERE.md               # Onboarding guide
├── QUICKSTART.md               # 3-step setup
├── QUICK_REFERENCE.md          # Command cheat sheet
├── GITHUB_DEPLOYMENT_GUIDE.md  # GitHub deployment walkthrough
└── APP_STORE_GUIDE.md          # App Store submission guide
```

---

## Dependencies

- [Toga](https://toga.readthedocs.io/) — Native Python GUI toolkit (iOS backend)
- [Briefcase](https://briefcase.readthedocs.io/) — Package Python projects as native apps
- [Requests](https://docs.python-requests.org/) — HTTP library
- [Web3.py](https://web3py.readthedocs.io/) — Ethereum interaction library

---

## Deployment

Refer to the included guides for detailed deployment instructions:

- **[START_HERE.md](START_HERE.md)** — Project overview and orientation
- **[QUICKSTART.md](QUICKSTART.md)** — Get running in 3 steps
- **[GITHUB_DEPLOYMENT_GUIDE.md](GITHUB_DEPLOYMENT_GUIDE.md)** — Full GitHub and CI/CD setup
- **[APP_STORE_GUIDE.md](APP_STORE_GUIDE.md)** — iPhone testing and App Store submission

---

## CI/CD

The GitHub Actions workflow (`.github/workflows/build.yml`) runs on every push to `main`:

1. Checks out the repository
2. Sets up Python
3. Installs Briefcase
4. Builds the iOS app
5. Uploads the IPA artifact

---

## License

MIT

---

*Built with Mythos Bridge and Terminal — Monico iOS v2.5*
