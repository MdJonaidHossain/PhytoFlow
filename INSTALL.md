# PhytoFlow Installation Guide

## 🚀 Quick Install (Recommended)

### Method 1: Smart Installer (Auto-detects your platform)

```bash
# Clone repository
git clone https://github.com/MdJonaidHossain/PhytoFlow.git
cd PhytoFlow

# Run smart installer
python install.py
```

The installer will:
- ✅ Auto-detect your platform (macOS/Linux/Windows)
- ✅ Detect available GPU (NVIDIA/AMD/Apple/Intel)
- ✅ Recommend optimal environment
- ✅ Install all dependencies
- ✅ Configure GPU acceleration automatically

---

## 📦 Manual Installation by Platform

Choose the environment file for your system:

### macOS Apple Silicon (M1/M2/M3/M4 Max/Ultra)
```bash
conda env create -f environment_mac_arm.yml
conda activate phytoflow_mac_arm
```
**Features**: MLX GPU acceleration (6-9x faster)

### macOS Intel
```bash
conda env create -f environment_mac_intel.yml
conda activate phytoflow_mac_intel
```
**Features**: CPU-only with MKL optimization (3-4x faster)

### Linux with NVIDIA GPU
```bash
conda env create -f environment_linux_nvidia.yml
conda activate phytoflow_linux_nvidia
```
**Features**: CUDA GPU acceleration (20-50x faster)

### Linux with AMD GPU
```bash
conda env create -f environment_linux_amd.yml
conda activate phytoflow_linux_amd
```
**Features**: ROCm GPU acceleration (15-25x faster)

### Linux CPU-only
```bash
conda env create -f environment_linux_cpu.yml
conda activate phytoflow_linux_cpu
```
**Features**: OpenBLAS optimization (3-4x faster)

### Linux ARM64 (Raspberry Pi, ARM servers)
```bash
conda env create -f environment_linux_arm.yml
conda activate phytoflow_linux_arm
```
**Features**: ARM-optimized (works on Raspberry Pi 4+)

### Windows with NVIDIA GPU
```bash
conda env create -f environment_windows_nvidia.yml
conda activate phytoflow_windows_nvidia
```
**Features**: CUDA GPU acceleration (20-50x faster)

### Windows CPU-only
```bash
conda env create -f environment_windows_cpu.yml
conda activate phytoflow_windows_cpu
```
**Features**: MKL optimization (3-4x faster)

---

## 🏃 Running PhytoFlow

After installation:

```bash
# Activate your environment (if using conda)
conda activate phytoflow_<your_platform>

# Run the app
streamlit run src/app.py
```

App opens at `http://localhost:8501` in <5 seconds!

---

## 🔧 Troubleshooting

### MLX Installation Issues (macOS Apple Silicon)

**Problem**: `ERROR: Could not find a version that satisfies the requirement mlx`

**Solutions**:

1. **Update pip first** (most common fix):
   ```bash
   python3 -m pip install --upgrade pip setuptools wheel
   python3 -m pip install mlx
   ```

2. **Check you're on Apple Silicon**:
   ```bash
   uname -m  # Should show: arm64
   ```
   If it shows `x86_64`, you're on Intel Mac - use `environment_mac_intel.yml` instead.

3. **Check Python version**:
   ```bash
   python3 --version  # Need 3.10 or later
   ```

4. **Conda environment with old pip**:
   ```bash
   conda activate your_env
   pip install --upgrade pip setuptools wheel
   pip install mlx
   ```

### Conda Not Found

**Install Miniconda** (lightweight, recommended):
- macOS/Linux: https://docs.conda.io/en/latest/miniconda.html
- Windows: Download installer from link above

Or use **Miniforge** (better for Apple Silicon):
```bash
# macOS Apple Silicon
brew install miniforge
```

### GPU Not Detected

Run diagnostic tool:
```bash
python diagnose_gpu.py
```

This will:
- Check your platform
- Detect available GPUs
- Test GPU libraries
- Provide specific fix instructions

---

## 📊 What Gets Installed

All environments include:

**Core Scientific Stack:**
- NumPy, SciPy, Pandas (numerical computing)
- Streamlit (GUI framework)
- Altair, Plotly (interactive visualization)

**Geometry & 3D:**
- Shapely (2D geometry)
- Trimesh (3D mesh operations)

**Image Processing (Optional):**
- OpenCV (computer vision)
- scikit-image (image analysis)

**Optimization:**
- CMA-ES (evolutionary algorithms)
- scipy.optimize (numerical optimization)

**GPU Acceleration (Platform-specific):**
- MLX (macOS Apple Silicon only)
- CuPy-CUDA (NVIDIA GPUs)
- CuPy-ROCm (AMD GPUs)
- dpnp (Intel GPUs)

**Testing:**
- pytest (unit testing)
- pytest-cov (coverage)

---

## 🎯 Performance Expectations

| Platform | Installation Time | App Startup | Simulation Speed |
|----------|------------------|-------------|------------------|
| **macOS M4 Max + MLX** | 5-8 min | <5s | 0.6s (8.7x faster) |
| **Linux + NVIDIA RTX 4090** | 10-15 min | <5s | 0.15s (35x faster) |
| **Windows + NVIDIA RTX 4090** | 10-15 min | <5s | 0.15s (35x faster) |
| **Linux + AMD RX 7900** | 10-15 min | <5s | 0.25s (21x faster) |
| **Any platform CPU-only** | 5-8 min | <5s | 1.5s (3.5x faster) |

*Simulation benchmark: 100 nodes, 1000 timesteps*

---

## 🆘 Getting Help

1. **Run Smart Installer**: `python install.py` - auto-detects and guides
2. **Run Diagnostic**: `python diagnose_gpu.py` - checks GPU setup
3. **Check Documentation**:
   - `README.md` - Quick start
   - `GPU_SETUP.md` - Detailed GPU instructions
   - `CROSS_PLATFORM.md` - Platform-specific notes
4. **Open Issue**: https://github.com/MdJonaidHossain/PhytoFlow/issues

---

## ✨ Minimal Installation (For Testing)

If you just want to test quickly without conda:

```bash
# Install minimal dependencies
pip install -r requirements.txt

# Run app
streamlit run src/app.py
```

This works on any platform but may be slower and won't include GPU acceleration.

---

## 🔄 Updating PhytoFlow

```bash
# Pull latest changes
git pull

# Update conda environment
conda env update -f environment_<your_platform>.yml

# Or update pip packages
pip install --upgrade -r requirements.txt
```

---

## 🗑️ Uninstalling

```bash
# Remove conda environment
conda env remove -n phytoflow_<your_platform>

# Or just delete the folder
rm -rf PhytoFlow
```

---

**💡 Pro Tip**: Use the smart installer (`python install.py`) - it handles everything automatically and chooses the best setup for your hardware!
