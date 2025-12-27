#!/usr/bin/env python3
"""
PhytoFlow GPU Diagnostic Tool

This script helps diagnose GPU installation issues and provides specific
recommendations for your hardware and Python environment.

Usage:
    python diagnose_gpu.py
"""

import sys
import platform
import subprocess
import os


def print_header(text):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f" {text}")
    print("=" * 70)


def print_check(name, status, detail=""):
    """Print a check result."""
    symbol = "✅" if status else "❌"
    print(f"{symbol} {name}: {detail}")


def check_python_version():
    """Check if Python version is compatible with GPU libraries."""
    print_header("Python Environment")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print_check("Python Version", True, version_str)
    
    # Check if version is compatible
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print_check("Version Compatible with MLX", False, 
                   "MLX requires Python 3.10+. Please upgrade Python.")
        return False
    else:
        print_check("Version Compatible with MLX", True, "Python 3.10+ detected")
        return True


def check_platform():
    """Check the platform and architecture."""
    print_header("Platform Information")
    
    sys_name = platform.system()
    machine = platform.machine()
    
    print_check("Operating System", True, sys_name)
    print_check("Architecture", True, machine)
    
    # Determine expected GPU type
    if sys_name == "Darwin" and machine == "arm64":
        print_check("Expected GPU Type", True, "Apple Silicon (Metal)")
        return "apple"
    elif sys_name == "Linux":
        print("💡 On Linux, could have NVIDIA, AMD, or Intel GPU")
        return "linux"
    elif sys_name == "Windows":
        print("💡 On Windows, could have NVIDIA, AMD, or Intel GPU")
        return "windows"
    else:
        print_check("Expected GPU Type", False, f"Unexpected platform: {sys_name}")
        return "unknown"


def check_pip():
    """Check pip version and update status."""
    print_header("Package Manager (pip)")
    
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"],
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            pip_version = result.stdout.strip()
            print_check("pip installed", True, pip_version)
            
            # Extract version number
            import re
            match = re.search(r'pip ([\d.]+)', pip_version)
            if match:
                version = match.group(1)
                major = int(version.split('.')[0])
                
                if major >= 21:
                    print_check("pip version", True, f"Version {version} is recent")
                    return True
                else:
                    print_check("pip version", False, 
                              f"Version {version} is outdated. Run: pip install --upgrade pip")
                    return False
        else:
            print_check("pip installed", False, "pip not found")
            return False
    
    except Exception as e:
        print_check("pip check", False, str(e))
        return False


def try_import_mlx():
    """Try to import MLX and report status."""
    print_header("Apple MLX (Metal GPU)")
    
    try:
        import mlx.core as mx
        print_check("MLX installed", True, f"Version {mx.__version__}")
        
        # Try to use MLX
        try:
            arr = mx.array([1, 2, 3])
            print_check("MLX functional", True, "Can create arrays on Metal GPU")
            return True
        except Exception as e:
            print_check("MLX functional", False, f"Import OK but runtime failed: {e}")
            return False
            
    except ImportError as e:
        print_check("MLX installed", False, "Not installed")
        print("\n💡 To install MLX:")
        print("   1. Update pip: pip install --upgrade pip setuptools wheel")
        print("   2. Install MLX: pip install mlx")
        return False
    except Exception as e:
        print_check("MLX check", False, str(e))
        return False


def try_import_cupy():
    """Try to import CuPy (NVIDIA/AMD)."""
    print_header("CuPy (NVIDIA CUDA / AMD ROCm)")
    
    try:
        import cupy as cp
        print_check("CuPy installed", True, f"Version {cp.__version__}")
        
        # Try to detect GPU
        try:
            device_count = cp.cuda.runtime.getDeviceCount()
            if device_count > 0:
                device_props = cp.cuda.runtime.getDeviceProperties(0)
                device_name = device_props['name'].decode('utf-8')
                print_check("GPU detected", True, f"{device_name} (CUDA)")
                return True
            else:
                print_check("GPU detected", False, "CuPy installed but no CUDA GPUs found")
                return False
        except Exception as e:
            print_check("GPU detection", False, f"Runtime error: {e}")
            return False
            
    except ImportError:
        print_check("CuPy installed", False, "Not installed")
        print("\n💡 To install CuPy:")
        print("   NVIDIA CUDA 12.x: pip install cupy-cuda12x")
        print("   NVIDIA CUDA 11.x: pip install cupy-cuda11x")
        print("   AMD ROCm 5.0:     pip install cupy-rocm-5-0")
        return False


def try_import_intel():
    """Try to import Intel oneAPI libraries."""
    print_header("Intel oneAPI (Intel Arc/Iris GPU)")
    
    try:
        import dpctl
        print_check("dpctl installed", True, f"Version {dpctl.__version__}")
        
        try:
            has_gpu = dpctl.has_gpu_devices()
            if has_gpu:
                print_check("Intel GPU detected", True, "oneAPI devices available")
                return True
            else:
                print_check("Intel GPU detected", False, "dpctl installed but no GPU found")
                return False
        except Exception as e:
            print_check("GPU detection", False, str(e))
            return False
            
    except ImportError:
        print_check("dpctl installed", False, "Not installed")
        print("\n💡 To install Intel GPU support:")
        print("   pip install dpctl dpnp")
        return False


def check_phytoflow():
    """Check if PhytoFlow can detect GPU."""
    print_header("PhytoFlow GPU Detection")
    
    try:
        # Add src to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        from accelerators import get_accelerator
        
        accel = get_accelerator()
        
        print(f"Device Type: {accel.device_type}")
        print(f"Device Name: {accel.device_name}")
        print(f"CPU Cores:   {accel.num_cores}")
        
        if accel.device_type != "cpu":
            print_check("PhytoFlow GPU Support", True, 
                       f"Using {accel.device_name}")
            return True
        else:
            print_check("PhytoFlow GPU Support", False, 
                       "No GPU detected, using CPU only")
            return False
            
    except Exception as e:
        print_check("PhytoFlow check", False, str(e))
        return False


def print_recommendations(platform_type, has_python, has_pip, has_gpu):
    """Print specific recommendations based on detected issues."""
    print_header("Recommendations")
    
    if not has_python:
        print("❗ CRITICAL: Python version too old")
        print("   → Upgrade to Python 3.10 or newer")
        print("   → macOS: brew install python@3.12")
        print("   → Linux: sudo apt install python3.12")
        print("   → Windows: Download from python.org")
        return
    
    if not has_pip:
        print("❗ IMPORTANT: Update pip first")
        print("   → Run: python3 -m pip install --upgrade pip setuptools wheel")
        return
    
    if not has_gpu:
        if platform_type == "apple":
            print("📱 For Apple Silicon (M1/M2/M3/M4):")
            print("   1. Update pip:    pip install --upgrade pip setuptools wheel")
            print("   2. Install MLX:   pip install mlx")
            print("   3. Verify:        python3 -c 'import mlx.core as mx; print(mx.__version__)'")
            print()
            print("   If still fails:")
            print("   • Check macOS version: sw_vers (need 13.5+)")
            print("   • Check architecture: uname -m (should be 'arm64')")
            print("   • Try in fresh venv: python3 -m venv venv && source venv/bin/activate")
        
        elif platform_type in ["linux", "windows"]:
            print("🖥️  For NVIDIA/AMD/Intel GPU:")
            print("   • NVIDIA: pip install cupy-cuda12x")
            print("   • AMD:    pip install cupy-rocm-5-0")
            print("   • Intel:  pip install dpctl dpnp")
            print()
            print("   Note: GPU drivers must be installed first!")
    else:
        print("✅ Everything looks good! GPU acceleration is working.")
        print()
        print("🚀 Launch PhytoFlow:")
        print("   streamlit run src/app.py")


def main():
    """Run all diagnostic checks."""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║           🔬 PhytoFlow GPU Diagnostic Tool                         ║
║                                                                    ║
║  This tool checks your system for GPU acceleration compatibility  ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Run checks
    has_python = check_python_version()
    platform_type = check_platform()
    has_pip = check_pip()
    
    # Try to detect installed GPU libraries
    has_mlx = try_import_mlx()
    has_cupy = try_import_cupy()
    has_intel = try_import_intel()
    
    has_gpu = has_mlx or has_cupy or has_intel
    
    # Check PhytoFlow integration
    check_phytoflow()
    
    # Print recommendations
    print_recommendations(platform_type, has_python, has_pip, has_gpu)
    
    print("\n" + "=" * 70)
    print(" Diagnostic Complete")
    print("=" * 70)
    
    if has_gpu:
        print("\n✅ GPU acceleration is available!")
    else:
        print("\n💡 No GPU detected - PhytoFlow will use multi-threaded CPU")
        print("   (This is fine for small simulations!)")


if __name__ == "__main__":
    main()
