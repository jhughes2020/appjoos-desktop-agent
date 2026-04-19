# Desktop Agent v0.1

A simple local desktop AI-agent starter project for monitoring system health, showing top processes, saving snapshots, and generating readable reports.

This version is intentionally **rule-based first**. It does not let AI invent system facts. The app gathers real machine data with `psutil`, analyzes it with clear thresholds, stores history in SQLite, and can optionally call a local Ollama model later for a friendlier summary.

## What this starter includes

- PySide6 desktop window
- Live CPU, memory, disk, and uptime metrics
- Top process table
- Rule-based findings and recommendations
- SQLite snapshot history
- Markdown report generator
- Optional Ollama client for local AI summaries later
- GitHub-friendly project structure

## Project structure

```text
desktop_agent_v0_1/
├── main.py
├── requirements.txt
├── README.md
├── docs/
│   └── GITHUB_SETUP.md
├── scripts/
│   ├── run_linux.sh
│   └── run_windows.bat
├── tests/
│   └── test_health_rules.py
└── desktop_agent/
    ├── app.py
    ├── ai/
    │   └── ollama_client.py
    ├── analyzers/
    │   └── health_rules.py
    ├── collectors/
    │   └── system_collector.py
    ├── config/
    │   └── settings.py
    ├── reports/
    │   └── generator.py
    ├── storage/
    │   └── db.py
    └── ui/
        └── main_window.py
```

## How to run it locally

### 1) Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install packages

```bash
pip install -r requirements.txt
```

### 3) Start the app

```bash
python main.py
```

## What you should see

- A desktop window titled **Desktop Agent v0.1**
- Health score at the top
- Four metric cards for CPU, memory, disk, and uptime
- Findings and recommendations box
- Top processes table
- Recent history box

## Main workflow

1. Open the app.
2. Let it refresh live metrics every few seconds.
3. Click **Save Snapshot** to write a point-in-time record into SQLite.
4. Click **Generate Report** to create a markdown report in the `reports/` folder.
5. Review the history panel to compare saved snapshots.

## How the logic works

### Collector layer
The collector uses `psutil` to ask the operating system for metrics such as:
- CPU percentage
- memory usage
- disk usage
- network counters
- boot time
- running processes

### Analyzer layer
The analyzer checks thresholds such as:
- high CPU usage
- high memory usage
- low free disk
- heavy top process

It then creates findings like:
- severity
- category
- message
- recommendation

### Storage layer
The database manager writes:
- `snapshots`
- `process_samples`
- `findings`

### Report layer
The report generator writes a simple markdown report you can share or commit to GitHub.

## Recommended next upgrades

### Version 0.2
- trend charts
- compare current snapshot vs previous snapshot
- configurable thresholds from the UI
- export JSON and CSV

### Version 0.3
- add Ollama-based local summaries
- add a natural-language question panel
- explain changes since the previous snapshot

### Version 0.4
- plugin system for custom collectors
- Windows event log collector
- battery/thermal collector where supported
- profile modes like gamer, creator, office workstation

## Optional: package as an executable

After the app works from source, install PyInstaller and build it:

```bash
pip install pyinstaller
pyinstaller --name DesktopAgent --windowed main.py
```

Your packaged output should appear in `dist/`.

## Basic troubleshooting

### Problem: `python` command is not found
Make sure Python is installed and available in your PATH.

### Problem: virtual environment does not activate
Try opening a new terminal in the project folder and run the activation command again.

### Problem: PySide6 import fails
Check that your virtual environment is active, then reinstall requirements.

### Problem: app opens but no history appears
History only appears after you click **Save Snapshot** at least once.

## Good GitHub practice for this project

- commit working changes in small steps
- keep the `README.md` updated
- do not commit your virtual environment folder
- do not commit local database files unless you intentionally want demo data in the repo
- add screenshots later to make the repo easier to understand

See `docs/GITHUB_SETUP.md` for a simple GitHub workflow.

## References

These are the main references used for the architecture and setup:

- Qt for Python / PySide6: https://doc.qt.io/qtforpython-6/
- Qt Widgets overview: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/index.html
- psutil docs: https://psutil.readthedocs.io/
- Python sqlite3 docs: https://docs.python.org/3/library/sqlite3.html
- Python venv docs: https://docs.python.org/3/library/venv.html
- Python packaging/installing modules: https://docs.python.org/3/installing/index.html
- PyInstaller docs: https://pyinstaller.org/en/stable/
- PyInstaller operating mode: https://pyinstaller.org/en/stable/operating-mode.html
- Ollama API intro: https://docs.ollama.com/api/introduction
- Ollama local auth note: https://docs.ollama.com/api/authentication
- GitHub README guidance: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes
- GitHub repository best practices: https://docs.github.com/en/repositories/creating-and-managing-repositories/best-practices-for-repositories
