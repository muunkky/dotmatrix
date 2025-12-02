# Documentation Card

## Overview

Document the testing strategy, test organization, and testing patterns used in the dotmatrix project.

**Documentation Type:** Developer Guide
**Target Audience:** Developers, Contributors
**Estimated Effort:** 1 day

## Scope

### What Will Be Documented

* [ ] Test organization and structure (tests/ directory layout)
* [ ] Types of tests (unit, integration, benchmarks)
* [ ] How to run tests (pytest commands, coverage)
* [ ] Fixtures and test utilities
* [ ] Mocking patterns (especially for GPU tests)
* [ ] Test data and demo files usage
* [ ] Adding new tests - patterns to follow

### Success Criteria

| Criterion | How to Verify |
| :--- | :--- |
| Test structure documented | Map of tests/ directory explained |
| Run commands provided | All test commands work as documented |
| Patterns explained | Common test patterns have examples |
| GPU testing explained | How GPU tests handle missing GPU |

### Dependencies

| Dependency | Status | Blocker? |
| :--- | :--- | :---: |
| Architecture Deep Dive spike (4ftn9c) | Provides test overview | No |
| Module Docstring Audit (mskwrn) | Test module docs | No |

## Implementation Plan

### Tasks

* [ ] Inventory all test files in tests/ (37 files)
* [ ] Categorize tests by module/feature being tested
* [ ] Document pytest configuration (conftest.py, pytest.ini)
* [ ] Document fixtures and their purposes
* [ ] Document benchmark tests (benchmarks/ directory)
* [ ] Document coverage configuration and reporting
* [ ] Add section on writing new tests

### Documentation Structure

```
docs/testing-guide.md
├── Overview
│   ├── Test Philosophy
│   └── Quick Start
├── Running Tests
│   ├── Basic Commands
│   ├── Coverage Reports
│   └── Benchmarks
├── Test Organization
│   ├── Unit Tests
│   ├── Integration Tests
│   └── GPU Tests
├── Fixtures & Utilities
├── Writing New Tests
│   ├── Patterns to Follow
│   └── GPU Mocking
└── Continuous Integration
```

## Notes

This is a P2 card - useful for contributors but not critical for initial handoff. The test suite is relatively well-organized already, this is about making that structure explicit and documented.

Review existing test files for patterns: test_cli.py, test_gpu.py, test_cluster_*.py for GPU mocking examples.
