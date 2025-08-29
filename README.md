# Stage RAM PFA Data Visualisation

# Dashboard Application

This repository provides an interactive Dash-based data visualization dashboard for analyzing RAM delay metrics and performance insights for Stage PFA. It includes both a web server and a desktop application build.

## Table of Contents

- [Features](#features)
- [Folder Structure](#folder-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Running the Server](#running-the-server)
  - [Building the Desktop App](#building-the-desktop-app)
  - [Docker Deployment](#docker-deployment)
- [Scripts](#scripts)
- [Contributing](#contributing)
- [License](#license)

## Features

- Multiple interactive pages: Home, Analytics, Weekly Analysis, Performance Metrics, Settings, About
- Automatic Excel data watcher with live updates
- Customizable settings via `dashboard/configurations/config.toml`
- Logging for server and desktop application events
- Build scripts for Python package, desktop installer, and Docker containers

## Folder Structure

```
.
├── dashboard/                # Dash application source code
│   ├── components/           # UI components (navbar, title, filters, etc.)
│   ├── pages/                # Page modules with metadata and layouts
│   ├── calculations/         # Data processing and performance metrics
│   ├── data_managers/        # Excel loader and directory watcher
│   ├── schemas/              # Pydantic schemas and types
│   ├── configurations/       # App & logging configuration
│   ├── utils_dashboard/      # Shared utilities (graphs, filters)
│   └── RAM Delay Dashboard.py# Main server entry point
├── build/                    # Installer scripts and build artifacts
├── logs/                     # Application log files
├── build_App.ps1            # Build Python package
├── build_desktop.ps1        # Create desktop installer via PyInstaller
├── build_docker.ps1         # Build Docker image
├── build_docker_compose.ps1 # Build Docker Compose setup
├── start_docker.ps1         # Launch Docker containers
├── run_server.windows.ps1   # Run Dash server on Windows
├── run_server.unix.ps1      # Run Dash server on Unix
├── main.spec                # PyInstaller spec file
├── pyproject.toml           # Python project metadata
└── README.md                # This file
```

## Installation

### Prerequisites

- Python 3.8+
- [Poetry](https://python-poetry.org/) for dependency management
- PowerShell (Windows) or Bash (Unix)
- Docker & Docker Compose (optional)

```powershell
# Clone the repository
git clone https://github.com/crazytajdine/Stage_Ram_PFA_Data_Visualisation.git
cd Stage_Ram_PFA_Data_Visualisation

# Install dependencies via Poetry
poetry install
```

## Configuration

Customize `dashboard/configurations/config.toml`:

```toml
dir_path = ""        # path to your data directory

[app]
app_name = "DashboardApp"
auth     = "StagePFA"

[exe]
name_of_python_exe = "server_dashboard"
```

## Usage

### Running the Server

```powershell
./run_server.windows.ps1   # Windows PowerShell
```

```bash
# Unix / Bash
./run_server.unix.ps1
```

Or directly via Poetry:

```bash
poetry run python "dashboard/RAM Delay Dashboard.py"
```

Open http://127.0.0.1:8050 in your browser.

### Building the Desktop App

```powershell
./build_desktop.ps1
```

The executable will be in the `dist/` directory.

### Docker Deployment

```powershell
./start_docker.ps1
```

This launches the dashboard within Docker containers.

## Scripts

- **build_App.ps1**: Package as a Python distribution
- **build_desktop.ps1**: PyInstaller desktop build
- **build_docker\*.ps1**: Docker image and Compose builds
- **start_docker.ps1**: Run Docker environment
- **run_server.\*.ps1**: Start Dash server

## Contributing

Contributions are welcome! Please open issues or submit pull requests.

## License

MIT © 2025 Taj Eddine Marmoul
