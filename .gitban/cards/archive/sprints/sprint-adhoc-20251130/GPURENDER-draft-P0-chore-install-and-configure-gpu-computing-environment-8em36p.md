# Install and Configure GPU Computing Environment

## Overview

Set up the GPU computing environment based on findings from the framework selection spike (79itcc).

## Prerequisites

- Completed spike 79itcc (GPU Framework Selection)
- GTX 1080 with driver 560.94 installed
- WSL2 environment

## Tasks

- [ ] Install CUDA toolkit (if CuPy route chosen)
- [ ] OR Install Numba with CUDA support (if Numba route chosen)
- [ ] Verify GPU is accessible from Python
- [ ] Run hello-world GPU computation
- [ ] Document installation steps in README or docs/
- [ ] Add GPU dependencies to pyproject.toml (optional extras)

## Verification

```python
# Test script to verify GPU setup
import [chosen_framework]
# Create array on GPU
# Perform simple operation
# Verify result
print("GPU setup successful!")
```

## Known Issues to Address

1. CuPy needs: libnvrtc.so.12, libcublas.so.12, libcurand.so.10
2. CUDA toolkit may need environment variable setup
3. WSL2 may need specific CUDA configuration

## Dependencies

- Spike 79itcc (must be completed first to know which framework)

## Notes

Installation steps will vary based on spike findings.
