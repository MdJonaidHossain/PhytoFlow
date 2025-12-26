# Cross-Platform Compatibility Guide

PhytoFlow is designed to work seamlessly across all major platforms:
- **macOS** (Intel and Apple Silicon ARM)
- **Linux** (x86_64, ARM64)
- **Windows** (x86_64)

## Platform-Specific Notes

### macOS (Apple Silicon / M1/M2/M3)

#### Known Issues & Solutions

1. **NumPy/SciPy Installation**
   - Apple Silicon requires native ARM builds
   - Solution: Use conda or pip with `--no-binary` flag if needed
   ```bash
   # Recommended: Use conda for Apple Silicon
   conda install numpy scipy pandas
   ```

2. **OpenCV**
   - Use opencv-python-headless for better compatibility
   ```bash
   pip install opencv-python-headless
   ```

3. **Trimesh with macOS**
   - Works natively on Apple Silicon
   - No special configuration needed

#### Installation (macOS ARM)
```bash
# Option 1: Using Homebrew Python
brew install python@3.10
python3.10 -m pip install -r requirements.txt

# Option 2: Using Conda (Recommended)
conda create -n phytoflow python=3.10
conda activate phytoflow
conda install numpy scipy pandas matplotlib
pip install -r requirements.txt
```

### Linux (x86_64 / ARM64)

#### Distribution-Specific Notes

**Ubuntu/Debian:**
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3-dev python3-pip
sudo apt-get install libgl1-mesa-glx  # For OpenCV

# Install PhytoFlow
pip3 install -r requirements.txt
```

**Fedora/RHEL/CentOS:**
```bash
sudo dnf install python3-devel python3-pip
sudo dnf install mesa-libGL  # For OpenCV
pip3 install -r requirements.txt
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip
pip install -r requirements.txt
```

#### ARM64 Linux (Raspberry Pi, Jetson, etc.)
- All dependencies support ARM64
- May require building from source for PyTorch (optional)
- Streamlit works natively

### Windows (x86_64)

#### Installation Steps

1. **Install Python 3.9+**
   - Download from python.org
   - ☑️ Check "Add Python to PATH"

2. **Install Visual C++ Build Tools** (if needed for compilation)
   - Download from Microsoft
   - Required for some native extensions

3. **Install Dependencies**
   ```cmd
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

#### Windows-Specific Issues

1. **Path Separators**
   - PhytoFlow uses `pathlib.Path` for cross-platform paths
   - All file operations are platform-agnostic

2. **Line Endings**
   - Git configured to handle CRLF/LF conversion
   - Python handles both automatically

3. **Long Path Names**
   - Enable long paths in Windows 10/11:
   ```cmd
   reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1
   ```

## Dependency Compatibility Matrix

| Package | macOS Intel | macOS ARM | Linux x86 | Linux ARM | Windows |
|---------|-------------|-----------|-----------|-----------|---------|
| streamlit | ✅ | ✅ | ✅ | ✅ | ✅ |
| numpy | ✅ | ✅ | ✅ | ✅ | ✅ |
| scipy | ✅ | ✅ | ✅ | ✅ | ✅ |
| pandas | ✅ | ✅ | ✅ | ✅ | ✅ |
| shapely | ✅ | ✅ | ✅ | ✅ | ✅ |
| trimesh | ✅ | ✅ | ✅ | ✅ | ✅ |
| altair | ✅ | ✅ | ✅ | ✅ | ✅ |
| opencv-python | ✅ | ✅ | ✅ | ✅ | ✅ |
| scikit-image | ✅ | ✅ | ✅ | ✅ | ✅ |
| scikit-optimize | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| torch (optional) | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| torch-geometric (optional) | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| deepxde (optional) | ✅ | ✅ | ✅ | ⚠️ | ✅ |

✅ = Fully supported  
⚠️ = Supported but may require manual build

## Testing Cross-Platform Compatibility

### Run Platform Tests
```bash
# All platforms
pytest tests/ -v

# Test on current platform
python -c "import platform; print(f'Platform: {platform.system()} {platform.machine()}')"
python -c "import sys; print(f'Python: {sys.version}')"

# Verify key imports
python -c "import streamlit, numpy, scipy, pandas, shapely, trimesh, altair; print('All imports successful!')"
```

### Known Platform Differences

1. **File Paths**
   - Uses `pathlib.Path` throughout
   - Automatically handles `/` vs `\` separators

2. **Temporary Files**
   - Uses `tempfile` module for platform-appropriate temp directories
   - On Windows: `%TEMP%`
   - On macOS/Linux: `/tmp` or `$TMPDIR`

3. **Process Management**
   - Streamlit server works identically across platforms
   - Port 8501 default on all platforms

4. **Floating Point Precision**
   - Uses `numpy.float64` for consistency
   - Numerical results identical across platforms

## Optional ML Dependencies

### PyTorch (for PINN/GNN features)

**macOS ARM:**
```bash
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

**Linux:**
```bash
# CPU-only
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# CUDA (if available)
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

**Windows:**
```cmd
REM CPU-only
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

REM CUDA (if available)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### PyTorch Geometric

```bash
# All platforms (after PyTorch is installed)
pip install torch-geometric
```

### DeepXDE

```bash
# All platforms
pip install deepxde
```

## Performance Notes

### Apple Silicon vs Intel

- **NumPy/SciPy**: Apple Silicon (ARM) often 2-3x faster than Intel for matrix operations
- **OpenCV**: Similar performance
- **Streamlit**: Identical UX

### GPU Acceleration (Optional)

- **Linux/Windows with NVIDIA GPU**: CUDA-enabled PyTorch significantly speeds up PINN/GNN training
- **macOS**: Metal GPU support in PyTorch for M1/M2/M3 chips
- **Core PhytoFlow**: Runs entirely on CPU, GPU not required

## Troubleshooting

### ImportError: DLL load failed (Windows)

**Solution:**
```cmd
pip install --upgrade --force-reinstall numpy scipy
```

### ImportError: Symbol not found (macOS)

**Solution:**
```bash
# Reinstall with Rosetta emulation if needed
arch -x86_64 pip install [package]
```

### Segmentation fault (Linux)

**Solution:**
```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade
pip install --upgrade numpy scipy
```

## Docker Support

For maximum cross-platform consistency, use Docker:

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run app
CMD ["streamlit", "run", "src/app.py", "--server.headless=true"]
```

Build and run:
```bash
docker build -t phytoflow .
docker run -p 8501:8501 phytoflow
```

## CI/CD Testing

PhytoFlow uses GitHub Actions to test on:
- Ubuntu (latest)
- macOS (Intel)
- macOS (ARM, M1)
- Windows (latest)

All platforms pass the same test suite (45 tests).

## Reporting Platform-Specific Issues

When reporting bugs, please include:
```bash
python -c "
import platform
import sys
print(f'OS: {platform.system()} {platform.release()}')
print(f'Architecture: {platform.machine()}')
print(f'Python: {sys.version}')
print(f'Python Implementation: {sys.implementation.name}')
"
```

And package versions:
```bash
pip list | grep -E "streamlit|numpy|scipy|pandas|shapely|trimesh"
```
