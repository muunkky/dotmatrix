"""GPU acceleration utilities for dotmatrix.

This module provides GPU acceleration via CuPy for CUDA-enabled systems.
Falls back gracefully to CPU (NumPy) when GPU is unavailable.

Requirements:
- NVIDIA GPU with CUDA support
- cupy-cuda12x package (pip install dotmatrix[gpu])
- CUDA runtime libraries (installed via pip with cupy)

Usage:
    from dotmatrix.gpu import get_array_module, is_gpu_available

    xp = get_array_module(use_gpu=True)  # Returns cupy or numpy
    arr = xp.zeros((100, 100))  # Works on GPU or CPU
"""

import os
import sys
import ctypes
from typing import Tuple, Optional

# Try to set up CUDA library path before importing cupy
# This is needed because cupy looks for libnvrtc.so in standard paths
_cuda_lib_paths = []
_site_packages = None

# Find site-packages location
for path in sys.path:
    if 'site-packages' in path:
        nvidia_path = os.path.join(path, 'nvidia')
        if os.path.exists(nvidia_path):
            _site_packages = path
            break

if _site_packages:
    # Add NVIDIA CUDA library paths from pip packages
    _nvidia_libs = [
        'cuda_nvrtc/lib',
        'cuda_runtime/lib',
        'cublas/lib',
        'cufft/lib',
        'cusparse/lib',
    ]
    for lib_dir in _nvidia_libs:
        lib_path = os.path.join(_site_packages, 'nvidia', lib_dir)
        if os.path.exists(lib_path):
            _cuda_lib_paths.append(lib_path)

    # Update LD_LIBRARY_PATH if we found CUDA libs
    if _cuda_lib_paths:
        existing = os.environ.get('LD_LIBRARY_PATH', '')
        new_paths = ':'.join(_cuda_lib_paths)
        if existing:
            os.environ['LD_LIBRARY_PATH'] = f"{new_paths}:{existing}"
        else:
            os.environ['LD_LIBRARY_PATH'] = new_paths

        # Pre-load the libraries using ctypes so they're available
        # This is necessary because LD_LIBRARY_PATH changes after Python starts
        # don't affect dlopen() calls
        for lib_path in _cuda_lib_paths:
            nvrtc_path = os.path.join(lib_path, 'libnvrtc.so.12')
            if os.path.exists(nvrtc_path):
                try:
                    ctypes.CDLL(nvrtc_path, mode=ctypes.RTLD_GLOBAL)
                except Exception:
                    pass  # Will try next path or fail later
                break

# Now try to import cupy
_GPU_AVAILABLE = False
_GPU_ERROR = None

try:
    import cupy as cp
    # Test if CUDA is actually available
    if cp.cuda.is_available():
        # Try a simple operation to verify runtime works
        _test = cp.array([1, 2, 3])
        _ = _test + 1
        cp.cuda.Stream.null.synchronize()
        _GPU_AVAILABLE = True
        del _test
except ImportError as e:
    _GPU_ERROR = f"CuPy not installed: {e}"
except Exception as e:
    _GPU_ERROR = f"GPU initialization failed: {e}"

# Always import numpy as fallback
import numpy as np


def is_gpu_available() -> bool:
    """Check if GPU acceleration is available.

    Returns:
        True if CuPy is installed and CUDA is working.
    """
    return _GPU_AVAILABLE


def get_gpu_info() -> dict:
    """Get information about the GPU environment.

    Returns:
        Dictionary with GPU status, device info, and any errors.
    """
    info = {
        'gpu_available': _GPU_AVAILABLE,
        'error': _GPU_ERROR,
        'cuda_lib_paths': _cuda_lib_paths,
    }

    if _GPU_AVAILABLE:
        import cupy as cp
        device = cp.cuda.Device(0)
        info.update({
            'device_name': device.name if hasattr(device, 'name') else 'Unknown',
            'device_id': device.id,
            'compute_capability': device.compute_capability,
            'cupy_version': cp.__version__,
        })

        # Get memory info
        try:
            mempool = cp.get_default_memory_pool()
            info['gpu_memory_used'] = mempool.used_bytes()
            info['gpu_memory_total'] = mempool.total_bytes()
        except Exception:
            pass

    return info


def get_array_module(use_gpu: bool = True):
    """Get the appropriate array module (CuPy for GPU, NumPy for CPU).

    Args:
        use_gpu: If True and GPU available, return CuPy. Otherwise NumPy.

    Returns:
        cupy module if GPU requested and available, numpy otherwise.
    """
    if use_gpu and _GPU_AVAILABLE:
        import cupy as cp
        return cp
    return np


def to_gpu(arr: np.ndarray) -> 'cp.ndarray':
    """Transfer numpy array to GPU.

    Args:
        arr: NumPy array

    Returns:
        CuPy array on GPU

    Raises:
        RuntimeError: If GPU is not available
    """
    if not _GPU_AVAILABLE:
        raise RuntimeError(f"GPU not available: {_GPU_ERROR}")
    import cupy as cp
    return cp.asarray(arr)


def to_cpu(arr) -> np.ndarray:
    """Transfer array from GPU to CPU.

    Args:
        arr: CuPy or NumPy array

    Returns:
        NumPy array on CPU
    """
    if _GPU_AVAILABLE:
        import cupy as cp
        if isinstance(arr, cp.ndarray):
            return cp.asnumpy(arr)
    return np.asarray(arr)


def synchronize():
    """Wait for all GPU operations to complete.

    Call this before timing GPU operations or before transferring results
    to ensure all GPU kernels have finished.
    """
    if _GPU_AVAILABLE:
        import cupy as cp
        cp.cuda.Stream.null.synchronize()


def print_gpu_status():
    """Print GPU status information to stdout."""
    info = get_gpu_info()

    print("=" * 60)
    print("GPU Status")
    print("=" * 60)

    if info['gpu_available']:
        print(f"GPU Available: YES")
        print(f"Device: {info.get('device_name', 'Unknown')}")
        print(f"Compute Capability: {info.get('compute_capability', 'Unknown')}")
        print(f"CuPy Version: {info.get('cupy_version', 'Unknown')}")
        if 'gpu_memory_used' in info:
            used_mb = info['gpu_memory_used'] / (1024 * 1024)
            total_mb = info['gpu_memory_total'] / (1024 * 1024)
            print(f"Memory Pool: {used_mb:.1f} MB used / {total_mb:.1f} MB total")
    else:
        print(f"GPU Available: NO")
        print(f"Error: {info.get('error', 'Unknown')}")

    if info['cuda_lib_paths']:
        print(f"\nCUDA Library Paths ({len(info['cuda_lib_paths'])}):")
        for path in info['cuda_lib_paths'][:3]:  # Show first 3
            print(f"  {path}")
        if len(info['cuda_lib_paths']) > 3:
            print(f"  ... and {len(info['cuda_lib_paths']) - 3} more")

    print("=" * 60)


if __name__ == '__main__':
    print_gpu_status()
