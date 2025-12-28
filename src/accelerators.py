"""Hardware acceleration module for GPU and multi-core CPU support.

Supports:
- Apple Silicon (Metal Performance Shaders)
- NVIDIA GPUs (CUDA via CuPy)
- AMD GPUs (ROCm via CuPy)
- Intel GPUs (oneAPI via dpctl/dpnp)
- Multi-core CPU (NumPy with OpenBLAS/MKL threading)
"""

import numpy as np
import platform
import os
from typing import Optional, Dict, Any
from functools import wraps
import warnings


class HardwareAccelerator:
    """Detects and configures optimal hardware acceleration."""
    
    def __init__(self):
        self.device_type = "cpu"
        self.device_name = "CPU"
        self.backend = None
        self.num_cores = os.cpu_count() or 1
        
        # Detect and configure best available hardware
        self._detect_hardware()
        self._configure_threading()
    
    def _detect_hardware(self):
        """Detect available GPU/accelerator hardware - tries all options automatically."""
        system = platform.system()
        machine = platform.machine()
        
        # Try all GPU backends in order of preference
        # This ensures we use whatever GPU is available on the system
        
        # 1. Try Apple Metal (Apple Silicon M1/M2/M3/M4)
        if self._try_metal():
            return
        
        # 2. Try NVIDIA CUDA (most common GPU)
        if self._try_cuda():
            return
        
        # 3. Try AMD ROCm (AMD GPUs)
        if self._try_rocm():
            return
        
        # 4. Try Intel oneAPI (Intel Arc, Iris, etc.)
        if self._try_intel():
            return
        
        # 5. Default to optimized multi-core CPU
        self.device_type = "cpu"
        self.device_name = f"CPU ({self.num_cores} cores)"
        self.backend = np
        print(f"ℹ️  No GPU detected - using multi-threaded CPU with {self.num_cores} cores")
    
    def _try_metal(self) -> bool:
        """Try to initialize Apple Metal Performance Shaders."""
        try:
            # MLX is Apple's ML framework with Metal acceleration
            import mlx.core as mx
            self.device_type = "metal"
            self.device_name = "Apple Silicon (Metal GPU)"
            self.backend = mx
            print(f"✅ Detected: {self.device_name}")
            return True
        except ImportError:
            pass
        except Exception as e:
            print(f"⚠️  Apple Metal detection failed: {e}")
        
        return False
    
    def _try_cuda(self) -> bool:
        """Try to initialize NVIDIA CUDA via CuPy."""
        try:
            import cupy as cp
            # Check if CUDA is actually available
            device_count = cp.cuda.runtime.getDeviceCount()
            if device_count > 0:
                device_props = cp.cuda.runtime.getDeviceProperties(0)
                device_name = device_props['name'].decode('utf-8')
                
                self.device_type = "cuda"
                self.device_name = f"NVIDIA {device_name}"
                self.backend = cp
                print(f"✅ Detected: {self.device_name} (CUDA)")
                return True
        except ImportError:
            pass
        except Exception as e:
            print(f"⚠️  NVIDIA CUDA detection failed: {e}")
        
        return False
    
    def _try_rocm(self) -> bool:
        """Try to initialize AMD ROCm via CuPy."""
        try:
            import cupy as cp
            # ROCm uses CuPy with HIP backend
            # Check environment or try to query ROCm devices
            if 'HIP_VISIBLE_DEVICES' in os.environ or 'ROCR_VISIBLE_DEVICES' in os.environ or 'ROCM_HOME' in os.environ:
                self.device_type = "rocm"
                self.device_name = "AMD GPU (ROCm/HIP)"
                self.backend = cp
                print(f"✅ Detected: {self.device_name}")
                return True
            
            # Try to detect via HIP runtime
            try:
                device_count = cp.cuda.runtime.getDeviceCount()
                if device_count > 0 and 'HIP' in str(cp):
                    self.device_type = "rocm"
                    self.device_name = "AMD GPU (ROCm/HIP)"
                    self.backend = cp
                    print(f"✅ Detected: {self.device_name}")
                    return True
            except:
                pass
                
        except ImportError:
            pass
        except Exception as e:
            print(f"⚠️  AMD ROCm detection failed: {e}")
        
        return False
    
    def _try_intel(self) -> bool:
        """Try to initialize Intel GPU via oneAPI."""
        try:
            import dpnp
            import dpctl
            
            # Check for Intel GPU
            if dpctl.has_gpu_devices():
                devices = dpctl.get_devices()
                gpu_devices = [d for d in devices if d.is_gpu]
                if gpu_devices:
                    device_name = gpu_devices[0].name
                    self.device_type = "intel"
                    self.device_name = f"Intel {device_name}"
                    self.backend = dpnp
                    print(f"✅ Detected: {self.device_name} (oneAPI)")
                    return True
        except ImportError:
            pass
        except Exception as e:
            print(f"⚠️  Intel GPU detection failed: {e}")
        
        return False
    
    def _configure_threading(self):
        """Configure multi-threading for NumPy operations."""
        # Set environment variables before importing NumPy
        # These control BLAS/LAPACK threading
        num_threads = str(self.num_cores)
        
        # OpenBLAS (used by many NumPy distributions)
        os.environ['OPENBLAS_NUM_THREADS'] = num_threads
        os.environ['GOTO_NUM_THREADS'] = num_threads
        
        # MKL (Intel Math Kernel Library)
        os.environ['MKL_NUM_THREADS'] = num_threads
        os.environ['MKL_DYNAMIC'] = 'FALSE'
        
        # Generic BLAS
        os.environ['OMP_NUM_THREADS'] = num_threads
        os.environ['NUMEXPR_NUM_THREADS'] = num_threads
        
        # Confirm settings
        try:
            import numpy as np
            # Try to get BLAS info
            config = np.__config__.show() if hasattr(np.__config__, 'show') else None
        except:
            pass
    
    def get_array_module(self):
        """Get the appropriate array module (numpy, cupy, mlx, etc.)."""
        return self.backend
    
    def to_device(self, array: np.ndarray):
        """Transfer array to accelerator device."""
        if self.device_type == "cpu":
            return array
        elif self.device_type in ["cuda", "rocm"]:
            return self.backend.asarray(array)
        elif self.device_type == "metal":
            return self.backend.array(array)
        elif self.device_type == "intel":
            return self.backend.array(array)
        return array
    
    def to_numpy(self, array):
        """Transfer array back to NumPy (CPU)."""
        if self.device_type == "cpu":
            return array
        elif self.device_type in ["cuda", "rocm"]:
            return self.backend.asnumpy(array)
        elif self.device_type == "metal":
            return np.array(array)
        elif self.device_type == "intel":
            return self.backend.asnumpy(array)
        return np.asarray(array)
    
    def get_info(self) -> Dict[str, Any]:
        """Get hardware acceleration info."""
        return {
            'device_type': self.device_type,
            'device_name': self.device_name,
            'num_cpu_cores': self.num_cores,
            'system': platform.system(),
            'machine': platform.machine(),
            'python_version': platform.python_version(),
        }
    
    def print_info(self):
        """Print hardware acceleration status."""
        info = self.get_info()
        print("=" * 60)
        print("🚀 PhytoFlow Hardware Acceleration")
        print("=" * 60)
        print(f"Device Type:     {info['device_type'].upper()}")
        print(f"Device Name:     {info['device_name']}")
        print(f"CPU Cores:       {info['num_cpu_cores']}")
        print(f"System:          {info['system']} {info['machine']}")
        print(f"Python:          {info['python_version']}")
        
        if self.device_type == "cpu":
            print("\n💡 GPU Acceleration:")
            print("   No GPU detected. Using multi-threaded CPU.")
            print("   To enable GPU acceleration, install:")
            print("   • Apple Silicon: pip install mlx")
            print("   • NVIDIA:        pip install cupy-cuda12x")
            print("   • AMD:           pip install cupy-rocm-5-0")
            print("   • Intel:         pip install dpnp dpctl")
        else:
            print(f"\n✅ GPU Acceleration: ENABLED")
        
        print("=" * 60)


# Global accelerator instance
_accelerator: Optional[HardwareAccelerator] = None


def get_accelerator() -> HardwareAccelerator:
    """Get or create the global hardware accelerator instance."""
    global _accelerator
    if _accelerator is None:
        _accelerator = HardwareAccelerator()
    return _accelerator


def accelerated(func):
    """Decorator to automatically use hardware acceleration for array operations."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        accel = get_accelerator()
        xp = accel.get_array_module()
        
        # Replace np with accelerated backend in kwargs
        if 'xp' not in kwargs:
            kwargs['xp'] = xp
        
        result = func(*args, **kwargs)
        return result
    
    return wrapper


class ParallelProcessor:
    """Parallel processing utilities for independent computations."""
    
    @staticmethod
    def parallel_map(func, items, n_jobs=-1):
        """
        Apply function to items in parallel using all CPU cores.
        
        Args:
            func: Function to apply
            items: Iterable of items to process
            n_jobs: Number of parallel jobs (-1 = all cores)
        
        Returns:
            List of results
        """
        try:
            from joblib import Parallel, delayed
            
            if n_jobs == -1:
                n_jobs = os.cpu_count() or 1
            
            results = Parallel(n_jobs=n_jobs, prefer="threads")(
                delayed(func)(item) for item in items
            )
            return results
        except ImportError:
            # Fallback to sequential if joblib not available
            warnings.warn("joblib not installed, running sequentially. "
                         "Install with: pip install joblib")
            return [func(item) for item in items]
    
    @staticmethod
    def parallel_solve(solver_func, param_sets, n_jobs=-1):
        """
        Run multiple simulations in parallel with different parameters.
        
        Useful for:
        - Parameter sweeps
        - Optimization algorithms
        - Monte Carlo simulations
        
        Args:
            solver_func: Function that takes params dict and returns results
            param_sets: List of parameter dictionaries
            n_jobs: Number of parallel jobs (-1 = all cores)
        
        Returns:
            List of results
        """
        return ParallelProcessor.parallel_map(solver_func, param_sets, n_jobs)


def get_optimal_batch_size(array_size: int, device_type: str = None) -> int:
    """
    Calculate optimal batch size for given array size and device.
    
    Args:
        array_size: Total number of elements to process
        device_type: Device type (cpu, cuda, metal, etc.)
    
    Returns:
        Optimal batch size
    """
    if device_type is None:
        device_type = get_accelerator().device_type
    
    if device_type == "cpu":
        # CPU: smaller batches, more parallelism
        return min(array_size, 1000)
    elif device_type in ["cuda", "rocm", "metal", "intel"]:
        # GPU: larger batches to amortize kernel launch overhead
        return min(array_size, 10000)
    
    return array_size


def vectorize_loop(loop_func, n_iterations: int, use_gpu: bool = True):
    """
    Convert a loop into vectorized operations for GPU/multi-core acceleration.
    
    Args:
        loop_func: Function that would be called in a loop
        n_iterations: Number of loop iterations
        use_gpu: Whether to use GPU if available
    
    Returns:
        Vectorized result
    """
    accel = get_accelerator()
    
    if use_gpu and accel.device_type != "cpu":
        # Use GPU vectorization
        xp = accel.get_array_module()
        # Create range on GPU
        indices = xp.arange(n_iterations)
        # Vectorized execution
        results = loop_func(indices)
        return accel.to_numpy(results)
    else:
        # Use NumPy's built-in parallelization
        indices = np.arange(n_iterations)
        return loop_func(indices)


# Convenience functions for common operations
def accelerated_matmul(A, B):
    """Matrix multiplication with automatic hardware acceleration."""
    accel = get_accelerator()
    xp = accel.get_array_module()
    
    A_device = accel.to_device(A)
    B_device = accel.to_device(B)
    
    result = xp.matmul(A_device, B_device)
    
    return accel.to_numpy(result)


def accelerated_solve(A, b):
    """Linear system solve with automatic hardware acceleration."""
    accel = get_accelerator()
    xp = accel.get_array_module()
    
    A_device = accel.to_device(A)
    b_device = accel.to_device(b)
    
    if hasattr(xp, 'linalg'):
        result = xp.linalg.solve(A_device, b_device)
    else:
        # Fallback to NumPy
        result = np.linalg.solve(A, b)
        return result
    
    return accel.to_numpy(result)


if __name__ == "__main__":
    # Demo hardware detection
    accel = get_accelerator()
    accel.print_info()
    
    # Test acceleration
    print("\n🧪 Testing array operations...")
    A = np.random.rand(1000, 1000)
    B = np.random.rand(1000, 1000)
    
    import time
    start = time.time()
    C = accelerated_matmul(A, B)
    elapsed = time.time() - start
    
    print(f"✓ Matrix multiplication (1000×1000): {elapsed:.4f}s")
    print(f"  Using: {accel.device_name}")
