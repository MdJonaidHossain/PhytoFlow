#!/usr/bin/env python3
"""
PhytoFlow Smart Installer
Auto-detects your platform and guides you through optimal installation.
"""

import sys
import platform
import subprocess
import os
from pathlib import Path

def get_platform_info():
    """Detect detailed platform information."""
    system = platform.system()  # Linux, Darwin, Windows
    machine = platform.machine()  # x86_64, arm64, AMD64, aarch64
    python_version = platform.python_version()
    
    return {
        'system': system,
        'machine': machine,
        'python_version': python_version,
        'is_64bit': sys.maxsize > 2**32
    }

def check_conda():
    """Check if conda is installed."""
    try:
        result = subprocess.run(['conda', '--version'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def check_gpu():
    """Attempt to detect available GPU."""
    gpu_info = {
        'nvidia': False,
        'amd': False,
        'intel': False,
        'apple': False
    }
    
    # Check NVIDIA
    try:
        result = subprocess.run(['nvidia-smi'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            gpu_info['nvidia'] = True
    except:
        pass
    
    # Check AMD ROCm
    try:
        result = subprocess.run(['rocm-smi'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            gpu_info['amd'] = True
    except:
        pass
    
    # Check Apple Silicon
    info = get_platform_info()
    if info['system'] == 'Darwin' and info['machine'] == 'arm64':
        gpu_info['apple'] = True
    
    return gpu_info

def print_header():
    """Print installation header."""
    print("=" * 70)
    print("🌿 PhytoFlow Smart Installer")
    print("=" * 70)
    print()

def print_platform_summary(info, gpu):
    """Print detected platform information."""
    print("📊 Detected Platform:")
    print(f"  Operating System: {info['system']}")
    print(f"  Architecture: {info['machine']}")
    print(f"  Python Version: {info['python_version']}")
    print(f"  64-bit: {'Yes' if info['is_64bit'] else 'No'}")
    print()
    
    print("🎮 GPU Detection:")
    if gpu['nvidia']:
        print("  ✅ NVIDIA GPU detected (CUDA available)")
    if gpu['amd']:
        print("  ✅ AMD GPU detected (ROCm available)")
    if gpu['apple']:
        print("  ✅ Apple Silicon detected (Metal GPU available)")
    if not any(gpu.values()):
        print("  ℹ️  No GPU detected (CPU-only mode)")
    print()

def get_recommended_env(info, gpu):
    """Determine the recommended conda environment file."""
    system = info['system']
    machine = info['machine']
    
    # macOS Apple Silicon
    if system == 'Darwin' and machine == 'arm64':
        return 'environment_mac_arm.yml', 'macOS Apple Silicon with MLX GPU'
    
    # macOS Intel
    if system == 'Darwin' and machine == 'x86_64':
        return 'environment_mac_intel.yml', 'macOS Intel (CPU-only)'
    
    # Linux x86_64
    if system == 'Linux' and machine in ['x86_64', 'AMD64']:
        if gpu['nvidia']:
            return 'environment_linux_nvidia.yml', 'Linux with NVIDIA GPU (CUDA)'
        elif gpu['amd']:
            return 'environment_linux_amd.yml', 'Linux with AMD GPU (ROCm)'
        else:
            return 'environment_linux_cpu.yml', 'Linux CPU-only (OpenBLAS optimized)'
    
    # Linux ARM
    if system == 'Linux' and machine in ['arm64', 'aarch64']:
        return 'environment_linux_arm.yml', 'Linux ARM64 (Raspberry Pi, ARM servers)'
    
    # Windows
    if system == 'Windows':
        if gpu['nvidia']:
            return 'environment_windows_nvidia.yml', 'Windows with NVIDIA GPU (CUDA)'
        else:
            return 'environment_windows_cpu.yml', 'Windows CPU-only (MKL optimized)'
    
    return None, None

def install_with_conda(env_file):
    """Install using conda."""
    print(f"📦 Installing PhytoFlow using: {env_file}")
    print()
    
    # Extract environment name from file
    env_name = env_file.replace('environment_', '').replace('.yml', '')
    env_name = f"phytoflow_{env_name}"
    
    print(f"Creating conda environment: {env_name}")
    print("This may take 5-10 minutes...")
    print()
    
    try:
        # Create environment
        cmd = ['conda', 'env', 'create', '-f', env_file]
        result = subprocess.run(cmd, check=True)
        
        if result.returncode == 0:
            print()
            print("✅ Installation successful!")
            print()
            print("🚀 To activate and run PhytoFlow:")
            print(f"   conda activate {env_name}")
            print("   streamlit run src/app.py")
            print()
            return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ Conda not found. Please install Miniconda or Anaconda first.")
        return False

def install_with_pip():
    """Install using pip (fallback)."""
    print("📦 Installing PhytoFlow using pip...")
    print()
    
    try:
        # Upgrade pip
        print("Upgrading pip...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 
                       'pip', 'setuptools', 'wheel'], check=True)
        
        # Install requirements
        print("Installing dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 
                       'requirements.txt'], check=True)
        
        print()
        print("✅ Installation successful!")
        print()
        print("🚀 To run PhytoFlow:")
        print("   streamlit run src/app.py")
        print()
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False

def install_gpu_package(gpu_info, platform_info):
    """Guide user to install GPU package."""
    print()
    print("🎮 GPU Acceleration Setup")
    print("=" * 70)
    
    if gpu_info['apple']:
        print("Apple Silicon detected - Installing MLX for GPU acceleration...")
        print()
        try:
            # Check if we can install MLX
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 
                          'pip', 'setuptools', 'wheel'], check=True)
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'mlx'], 
                         check=True)
            print("✅ MLX installed successfully!")
            print("   Your simulations will be 6-9x faster!")
        except:
            print("⚠️  MLX installation failed. Using CPU-only mode.")
            print("   Try: python3 -m pip install --upgrade pip setuptools wheel")
            print("   Then: python3 -m pip install mlx")
    
    elif gpu_info['nvidia']:
        print("NVIDIA GPU detected - Installing CuPy for GPU acceleration...")
        print()
        print("Run one of these commands based on your CUDA version:")
        print("   pip install cupy-cuda12x  # For CUDA 12.x (RTX 40, A100, H100)")
        print("   pip install cupy-cuda11x  # For CUDA 11.x (RTX 30 series)")
        print()
        print("Check your CUDA version with: nvidia-smi")
    
    elif gpu_info['amd']:
        print("AMD GPU detected - Installing CuPy-ROCm for GPU acceleration...")
        print()
        print("Run one of these commands based on your ROCm version:")
        print("   pip install cupy-rocm-5-0  # For ROCm 5.x")
        print("   pip install cupy-rocm-6-0  # For ROCm 6.x")
        print()
        print("Check your ROCm version with: rocm-smi")
    
    print()

def show_manual_instructions(env_file, description):
    """Show manual installation instructions."""
    print()
    print("📖 Manual Installation Instructions")
    print("=" * 70)
    print()
    print(f"Recommended environment: {description}")
    print()
    print("Step 1: Install Conda (if not installed)")
    print("  Download from: https://docs.conda.io/en/latest/miniconda.html")
    print()
    print("Step 2: Create environment")
    print(f"  conda env create -f {env_file}")
    print()
    print("Step 3: Activate environment")
    env_name = env_file.replace('environment_', '').replace('.yml', '')
    print(f"  conda activate phytoflow_{env_name}")
    print()
    print("Step 4: Run PhytoFlow")
    print("  streamlit run src/app.py")
    print()

def main():
    """Main installation routine."""
    print_header()
    
    # Detect platform
    info = get_platform_info()
    gpu = check_gpu()
    
    print_platform_summary(info, gpu)
    
    # Get recommended environment
    env_file, description = get_recommended_env(info, gpu)
    
    if env_file is None:
        print("⚠️  Unsupported platform detected.")
        print("    Please install manually using: pip install -r requirements.txt")
        return
    
    print(f"💡 Recommended Setup: {description}")
    print(f"   Environment File: {env_file}")
    print()
    
    # Check if conda is available
    has_conda = check_conda()
    
    if has_conda:
        print("✅ Conda detected")
        print()
        
        # Ask user preference
        print("Choose installation method:")
        print("  1) Conda (recommended) - Full environment with all dependencies")
        print("  2) Pip - Minimal installation, manual GPU setup")
        print("  3) Show manual instructions")
        print()
        
        choice = input("Enter choice (1-3) [1]: ").strip() or "1"
        print()
        
        if choice == "1":
            if Path(env_file).exists():
                install_with_conda(env_file)
                if any(gpu.values()):
                    install_gpu_package(gpu, info)
            else:
                print(f"❌ Environment file not found: {env_file}")
                print("   Using pip installation instead...")
                install_with_pip()
        elif choice == "2":
            install_with_pip()
            if any(gpu.values()):
                install_gpu_package(gpu, info)
        else:
            show_manual_instructions(env_file, description)
    else:
        print("ℹ️  Conda not detected")
        print()
        print("Choose installation method:")
        print("  1) Pip installation (will install now)")
        print("  2) Show conda installation instructions")
        print()
        
        choice = input("Enter choice (1-2) [1]: ").strip() or "1"
        print()
        
        if choice == "1":
            install_with_pip()
            if any(gpu.values()):
                install_gpu_package(gpu, info)
        else:
            show_manual_instructions(env_file, description)
    
    print()
    print("=" * 70)
    print("📚 Additional Resources:")
    print("  - README.md: Quick start guide")
    print("  - GPU_SETUP.md: Detailed GPU installation")
    print("  - CROSS_PLATFORM.md: Platform-specific notes")
    print("  - Run 'python diagnose_gpu.py' to verify GPU setup")
    print("=" * 70)
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
