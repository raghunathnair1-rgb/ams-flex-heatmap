# AMS Flex-Date Flight Finder — Desktop

A thin Electron shell that opens the live app (https://ams-flex-heatmap.vercel.app)
in a native window — double-click the app, no browser tabs, no local server to
run. It's a window onto the deployed site, not a bundled copy, so it's always
up to date and stays inside the same guardrails/sandbox as the web app (the
Electron renderer has no Node integration, `contextIsolation: true`,
`sandbox: true`).

## Get a binary

Prebuilt binaries are attached to [GitHub Releases](../../releases) — built
by `.github/workflows/build-desktop.yml` on real macOS and Windows GitHub
Actions runners (not cross-compiled), one per platform:

- **macOS**: `AMS Flex-Date Flight Finder-*.dmg` — open it, drag the app to
  Applications, double-click to launch. (Unsigned build: first launch needs
  right-click → Open, or System Settings → Privacy & Security → "Open Anyway".)
- **Windows**: `AMS Flex-Date Flight Finder Setup *.exe` — one-click installer,
  adds a desktop shortcut.

## Build it yourself

```bash
cd desktop
npm install
npm run dist:mac   # on macOS -> dist/*.dmg
npm run dist:win   # on Windows -> dist/*.exe
```

Cross-building macOS binaries from Windows (or vice versa) isn't attempted
here — the CI matrix builds each on its native OS, which is the reliable path.

## Local dev (point at the dev server instead of production)

```bash
ELECTRON_START_URL=http://localhost:5173 npm start
```

## Regenerating the icon

```bash
cd ../  # repo root
source .venv/bin/activate
pip install pillow
python3 desktop/build/make_icon.py
```
