# M-Duino-PCSM
### Parameter Control and Status Monitoring

`M-Duino-PCSM` is the operator-facing application for supervising the `Industrial Shields M-Duino 19R+` controller used in the trigger-box workflow.

The app is intended to make it easier to:

- connect to the controller over USB
- monitor live status and state changes
- edit approved operator parameters between runs
- inspect firmware event output
- review the firmware source files stored in this repository

The laptop app is not the real-time firing controller. The firmware remains responsible for timing execution, sequence logic, safety checks, and hazardous-cycle behavior.

## What The App Covers

- backend selection between `Mock controller` and `USB serial`
- live status display for arm, trigger, spark, and DAQ signals
- operator parameter input and apply flow
- event and transition log review
- in-app firmware script viewer for the files in `M-DuinoScripts`

It is not intended to:

- replace embedded timing logic
- bypass firmware validation or lockout behavior
- directly drive hazardous hardware from the PC

## Main App Pages

- `Home`: purpose, quick start, backend explanation, and workflow summary
- `Controller Workspace`: connection controls, live status, parameter input, and event log
- `Firmware Scripts`: read-only viewer for the `.ino` files inside `M-DuinoScripts`

## 🚀 Quick Start

### ✅ Prerequisites

- Python `3.10+`
- `npm`
- Node.js `18+`

### ▶️ Recommended Launchers

Setup once:

- <img src="https://cdn.simpleicons.org/linux" alt="Linux" width="16" height="16"> Linux: [Setup-M-Duino-PCSM-LINUX.sh](/Volumes/Sim_Back_Up/M-Duino-PCSM/Setup-M-Duino-PCSM-LINUX.sh)
- <img src="https://cdn.simpleicons.org/apple" alt="macOS" width="16" height="16"> macOS: [Setup-M-Duino-PCSM-MAC.command](/Volumes/Sim_Back_Up/M-Duino-PCSM/Setup-M-Duino-PCSM-MAC.command)
- <img src="https://cdn.simpleicons.org/windows11" alt="Windows" width="16" height="16"> Windows: [Setup-M-Duino-PCSM-WIN.bat](/Volumes/Sim_Back_Up/M-Duino-PCSM/Setup-M-Duino-PCSM-WIN.bat)

Then run:

- <img src="https://cdn.simpleicons.org/linux" alt="Linux" width="16" height="16"> Linux: [Run-M-Duino-PCSM-LINUX.sh](/Volumes/Sim_Back_Up/M-Duino-PCSM/Run-M-Duino-PCSM-LINUX.sh)
- <img src="https://cdn.simpleicons.org/apple" alt="macOS" width="16" height="16"> macOS: [Run-M-Duino-PCSM-MAC.command](/Volumes/Sim_Back_Up/M-Duino-PCSM/Run-M-Duino-PCSM-MAC.command)
- <img src="https://cdn.simpleicons.org/windows11" alt="Windows" width="16" height="16"> Windows: [Run-M-Duino-PCSM-WIN.bat](/Volumes/Sim_Back_Up/M-Duino-PCSM/Run-M-Duino-PCSM-WIN.bat)

Unified launcher:

- Linux/macOS: [run](/Volumes/Sim_Back_Up/M-Duino-PCSM/run)

Example:

```bash
./run mduino
```

Default local app URL:

- [http://127.0.0.1:5174/?backendPort=5001](http://127.0.0.1:5174/?backendPort=5001)

## Manual Install

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install --no-build-isolation -e .
pip install -r backend/requirements.txt
npm install
```

## Manual Run

Start the backend:

```bash
source .venv/bin/activate
MDUINO_BACKEND_PORT=5001 python backend/app.py
```

In a second terminal:

```bash
npm run vite -- --host 127.0.0.1 --port 5174 --strictPort
```

Then open:

- [http://127.0.0.1:5174/?backendPort=5001](http://127.0.0.1:5174/?backendPort=5001)

## Most Useful Commands

```bash
# One-time setup
./Setup-M-Duino-PCSM-LINUX.sh

# Normal launcher
./Run-M-Duino-PCSM-LINUX.sh

# Frontend only
npm run vite -- --host 127.0.0.1 --port 5174 --strictPort

# Backend only
.venv/bin/python backend/app.py

# Frontend build
npm run build
```

## 🏗️ Architecture

### Frontend

- React + Vite browser app
- single-shell navigation with `Home`, `Controller Workspace`, and `Firmware Scripts`
- `AiRA` page for grounded repository questions and optional Ollama-backed responses
- operator-facing parameter and status workspace

Key files:

- [frontend/src/app/AppShell.jsx](/Volumes/Sim_Back_Up/M-Duino-PCSM/frontend/src/app/AppShell.jsx)
- [frontend/src/features/home/HomePage.jsx](/Volumes/Sim_Back_Up/M-Duino-PCSM/frontend/src/features/home/HomePage.jsx)
- [frontend/src/features/workspace/WorkspacePage.jsx](/Volumes/Sim_Back_Up/M-Duino-PCSM/frontend/src/features/workspace/WorkspacePage.jsx)
- [frontend/src/features/firmware/FirmwarePage.jsx](/Volumes/Sim_Back_Up/M-Duino-PCSM/frontend/src/features/firmware/FirmwarePage.jsx)

### Backend

- Flask API for controller state, parameters, and firmware file browsing
- AiRA context and query endpoints
- service abstraction for mock and serial backends

Key backend files:

- [backend/app.py](/Volumes/Sim_Back_Up/M-Duino-PCSM/backend/app.py)
- [mduino_pcsm/service_registry.py](/Volumes/Sim_Back_Up/M-Duino-PCSM/mduino_pcsm/service_registry.py)
- [mduino_pcsm/models.py](/Volumes/Sim_Back_Up/M-Duino-PCSM/mduino_pcsm/models.py)
- [mduino_pcsm/services/base.py](/Volumes/Sim_Back_Up/M-Duino-PCSM/mduino_pcsm/services/base.py)
- [mduino_pcsm/services/mock_controller.py](/Volumes/Sim_Back_Up/M-Duino-PCSM/mduino_pcsm/services/mock_controller.py)
- [mduino_pcsm/services/serial_controller.py](/Volumes/Sim_Back_Up/M-Duino-PCSM/mduino_pcsm/services/serial_controller.py)

## Firmware Context

The app is built around these repository firmware snapshots:

- [M-Duino_Original.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/M-Duino_Original/M-Duino_Original.ino)
- [M_Duino_v000.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/M_Duino_v000/M_Duino_v000.ino)
- [M_Duino_v001.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/M_Duino_v001/M_Duino_v001.ino)
- [M_Duino_v002.ino](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts/M_Duino_v002/M_Duino_v002.ino)

## Repository Layout

- [frontend/](/Volumes/Sim_Back_Up/M-Duino-PCSM/frontend): browser app
- [backend/](/Volumes/Sim_Back_Up/M-Duino-PCSM/backend): Flask API
- [mduino_pcsm/](/Volumes/Sim_Back_Up/M-Duino-PCSM/mduino_pcsm): controller models and services
- [Documentation/](/Volumes/Sim_Back_Up/M-Duino-PCSM/Documentation): project brief and supporting notes
- [M-DuinoScripts/](/Volumes/Sim_Back_Up/M-Duino-PCSM/M-DuinoScripts): firmware source snapshots
- [EXDA-app/](/Volumes/Sim_Back_Up/M-Duino-PCSM/EXDA-app): reference copy kept in the repo
- [VERSIONING.md](/Volumes/Sim_Back_Up/M-Duino-PCSM/VERSIONING.md): release and branch workflow

## Versioning

This repository uses git tags for releases.

See [VERSIONING.md](/Volumes/Sim_Back_Up/M-Duino-PCSM/VERSIONING.md) for the branch workflow and tag naming rules.

## 🤖 AiRA Notes

- AiRA always works in grounded local mode using `Documentation/` and `M-DuinoScripts/`
- If Ollama is reachable, AiRA can also answer with a local model and show the host/model used
- The Linux launcher reports either `AiRA / feature tooling: ready` or `AiRA / feature tooling: local grounded mode`

## 🛠️ Troubleshooting

- If setup has not been run yet, use the matching `Setup-M-Duino-PCSM-*` launcher first.
- If the browser app does not open automatically, run the `Run-M-Duino-PCSM-*` launcher again and open the printed URL manually.
- If EXDA is already using `5000` and `5173`, that is expected. This app now defaults to `5001` and `5174`.
- If no serial device appears, start with `Mock controller` to verify the UI flow first.
- If frontend dependencies are incomplete for the current machine, rerun setup so native packages reinstall correctly.
