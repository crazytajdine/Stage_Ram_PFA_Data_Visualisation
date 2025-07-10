# Tauri + Dash Application

A desktop application that combines Tauri (Rust) with Dash (Python) to create a modern sales dashboard with native desktop capabilities.

## Overview

This project demonstrates how to integrate a Python Dash web application within a Tauri desktop wrapper, providing the best of both worlds:
- Native desktop performance and security (Tauri/Rust)
- Rich data visualization capabilities (Dash/Plotly)
- Cross-platform compatibility

## Prerequisites

Before starting, make sure you have the following installed on your system:

### Required Software
1. **Python** (3.9 - 3.13)
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to add Python to your PATH during installation

2. **Poetry** (Python dependency manager)
   ```powershell
   # Install Poetry via pip
   pip install poetry
   
   # Or use the official installer (recommended)
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
   ```

3. **Rust** (for Tauri)
   ```powershell
   # Install Rust via rustup
   # Download and run: https://rustup.rs/
   ```

4. **Node.js** (for Tauri CLI)
   - Download from [nodejs.org](https://nodejs.org/)
   - Or use winget: `winget install OpenJS.NodeJS`

5. **Tauri CLI**
   ```powershell
   npm install 
   ```

## Project Structure

```
tauri-app/
├── dashboard/              # Python Dash application
│   ├── main.py            # Main Dash app
│   └── README.md
├── src-tauri/             # Tauri (Rust) backend
│   ├── src/
│   │   ├── main.rs        # Rust main file
│   │   └── lib.rs
│   ├── tauri.conf.json    # Tauri configuration
│   └── Cargo.toml
├── public/                # Static files
│   └── index.html         # Loading page
├── pyproject.toml         # Python dependencies
├── poetry.lock            # Locked Python dependencies
├── main.spec              # PyInstaller configuration
└── README.md              # This file
```

## Setup Instructions

### 1. Clone and Navigate to Project
```powershell
# If you haven't already, navigate to the project directory
cd ".\tauri-app"
```

### 2. Install Python Dependencies
```powershell
# Install Python dependencies using Poetry
poetry install
```

### 3. Install Rust Dependencies
```powershell
# Navigate to Tauri directory and install dependencies
cd src-tauri
cargo build
cd ..
```

### 4. Verify Installation
```powershell
# Check if Poetry environment is working
poetry run python --version

# Check if Tauri is working
tauri info
```

## Running the Application

### Development Mode

#### Option 1: Run Tauri Development Server (Recommended)
```powershell
# This will start both the Python Dash server and Tauri app
tauri dev
```

#### Option 2: Run Components Separately
```powershell
# Terminal 1: Start the Dash server
poetry run python dashboard/main.py

# Terminal 2: Start Tauri (in another terminal)
tauri dev
```

### Production Build

#### 1. Build Python Executable
```powershell
# Create standalone Python executable using PyInstaller
poetry run pyinstaller main.spec
```

#### 2. Build Tauri Application
```powershell
# Build the complete desktop application
tauri build
```

The built application will be available in `src-tauri/target/release/bundle/`

## Application Features

### Dashboard Features
- **Interactive Sales Visualization**: Line charts showing sales trends over time
- **Region Filtering**: Dropdown to filter data by geographic regions (North, South, East, West)
- **Real-time Statistics**: Display of average, maximum, and minimum sales values
- **Responsive Design**: Modern web interface that adapts to different window sizes

### Technical Features
- **Desktop Integration**: Native desktop application with system integration
- **Automatic Server Management**: Backend server starts automatically with the app
- **Cross-platform**: Runs on Windows, macOS, and Linux
- **Offline Capability**: Once built, runs without internet connection

## Configuration

### Tauri Configuration (`src-tauri/tauri.conf.json`)
- **Window Settings**: Default size (1000x700), resizable
- **Development URL**: Points to `http://localhost:8050` (Dash default)
- **Build Commands**: Automatically installs dependencies and builds Python executable

### Python Dependencies (`pyproject.toml`)
- **Dash**: Web application framework
- **Plotly**: Interactive visualization library
- **Pandas**: Data manipulation and analysis
- **PyInstaller**: Creates standalone executable

## Troubleshooting

### Common Issues

#### 1. Poetry not found
```powershell
# Make sure Poetry is in your PATH, or install it globally
pip install poetry
```

#### 2. Rust compilation errors
```powershell
# Update Rust toolchain
rustup update

# Clear cargo cache
cargo clean
```

#### 3. Python dependencies issues
```powershell
# Clear Poetry cache and reinstall
poetry cache clear . --all
poetry install
```

#### 4. Port 8050 already in use
```powershell
# Find and kill process using port 8050
netstat -ano | findstr :8050
# Note the PID and kill it
taskkill /PID <PID> /F
```

#### 5. Tauri build fails
```powershell
# Make sure all dependencies are installed
tauri info

# Try building step by step
cargo build --manifest-path=src-tauri/Cargo.toml
```

### Development Tips

1. **Hot Reload**: In development mode, both Rust and Python changes trigger automatic reloads
2. **Debugging**: Use browser dev tools by right-clicking in the app and selecting "Inspect"
3. **Logs**: Check console output for both Tauri and Dash application logs
4. **Performance**: Monitor memory usage in Task Manager during development

## Customization

### Adding New Features to Dashboard
1. Edit `dashboard/main.py` to add new visualizations or data sources
2. Update dependencies in `pyproject.toml` if needed
3. Test with `poetry run python dashboard/main.py`

### Modifying Tauri Configuration
1. Edit `src-tauri/tauri.conf.json` for app settings
2. Modify `src-tauri/src/main.rs` for Rust backend logic
3. Update icons in `src-tauri/icons/` directory

### Building for Distribution
1. Ensure all dependencies are correctly specified
2. Test the production build thoroughly
3. Consider code signing for Windows distribution

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly in both development and production modes
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review Tauri documentation: [tauri.app](https://tauri.app/)
3. Review Dash documentation: [dash.plotly.com](https://dash.plotly.com/)

---

**Note**: This application is designed to work on Windows, macOS, and Linux. The instructions above are specific to Windows PowerShell, but similar commands work on other platforms with appropriate shell syntax.