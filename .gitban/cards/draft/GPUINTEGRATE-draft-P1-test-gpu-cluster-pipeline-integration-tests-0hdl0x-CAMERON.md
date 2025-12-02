## Description

Add integration tests verifying that the GPU cluster functions are correctly integrated into the main pipeline and that the default CLI command uses GPU acceleration when available.

**Value**: Ensures GPU integration works correctly end-to-end and prevents regressions.

---

## Test Plan

### Integration Tests to Add

- [ ] Test `cluster_and_count_pixels()` GPU vs CPU equivalence on realistic data
- [ ] Test GPU path produces identical ClusterResult objects to CPU path
- [ ] Test `use_gpu=None` auto-detects GPU correctly
- [ ] Test `use_gpu=True` forces GPU path
- [ ] Test `use_gpu=False` forces CPU path
- [ ] Test default CLI uses GPU when available

### Test File Location

`tests/test_gpu_cluster_integration.py`

### Test Implementation

```python
class TestGPUClusterIntegration:
    """Test GPU cluster functions integrated into pipeline."""
    
    def test_cluster_and_count_gpu_cpu_equivalence(self):
        """Test GPU and CPU paths produce identical results."""
        # Create test masks
        # Run with use_gpu=True and use_gpu=False
        # Compare ClusterResult objects
        
    def test_default_cli_uses_gpu(self):
        """Test minimal CLI uses GPU when available."""
        # Run: python -m dotmatrix -i test.png
        # Verify GPU was used (check stderr for GPU messages)
```

---

## Acceptance Criteria

- [ ] test_gpu_cluster_integration.py exists with 5+ tests
- [ ] All tests pass with GPU available
- [ ] All tests pass with GPU unavailable (CPU fallback)
- [ ] Tests verify GPU/CPU equivalence within tolerance
