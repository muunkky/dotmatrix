# Deep Architectural Review Spike

## Spike Overview

* **Investigation Question:** What are the current architectural patterns, strengths, and technical debt in the dotmatrix codebase, and what principles should guide future development as we add more rendering methods and complexity?
* **Problem/Opportunity:** The project has grown incrementally with multiple rendering methods (flower, bullseye, block, treemap, exact, cmyk-blend), GPU acceleration, drift correction, and large file handling. Before adding more features (jitter, SVG, ASCII output), we need to understand the current architecture to ensure future changes follow consistent patterns and don't accumulate technical debt.
* **Time Box:** 1-2 days
* **Success Criteria:** 
  - Comprehensive architectural analysis document created
  - Key patterns identified and documented  
  - Technical debt catalogued with severity ratings
  - Architectural principles documented for future development
  - Refactoring opportunities identified and prioritized
  - Follow-up cards created for any critical issues
* **Priority:** P1 - Blocking further feature development
* **Related Work:** Related to ARCHREVIEW sprint, supports all documentation cards in this sprint

**Required Checks:**
* [x] **Investigation question** is specific and answerable.
* [x] **Time box** is defined (prevents endless investigation).
* [x] **Success criteria** clearly defines what \"done\" looks like.

---

## Context & Background Research

Before diving into investigation, review existing knowledge, related work, and available documentation.

* [x] Existing documentation reviewed (README.md, DEVELOPMENT.md, OPTIMAL_USAGE.md).
* [x] ADRs reviewed (8 ADRs found in docs/adr/).
* [x] Architecture docs reviewed (pipeline-overview.md, color-pipeline.md, system-overview-flowchart.md).
* [x] Codebase structure reviewed (src/dotmatrix/ modules).
* [x] Test suite reviewed (tests/ directory, coverage reports).

| Source Type | Link / Location | Key Findings / Relevant Context |
| :--- | :--- | :--- |
| **README.md** | Project root | Documents features, CLI usage, installation. Flower rendering mentioned. Comprehensive usage examples. |
| **DEVELOPMENT.md** | docs/DEVELOPMENT.md | Developer onboarding guide. Has project structure overview, testing instructions, GPU setup. |
| **ROADMAP.md** | Project root | Shows v0.2.0 complete, v0.3.0 in progress. 10 milestones planned through 2028. Very detailed. |
| **ADRs (8 total)** | docs/adr/ | Covers: large file processing, SVG output, CLI UX, jitter, scalability, block renderer, GPU acceleration, cluster rendering, pixel counting, logging, edge detection. Good coverage. |
| **Architecture Docs** | docs/architecture/ | Has pipeline-overview.md, color-pipeline.md, system-overview-flowchart.md. Documents core flows. |
| **Source Code** | src/dotmatrix/ | Main modules: cli.py, circle_detector.py, color_extractor.py, color_clustering.py, multiple renderers (circle_renderer.py, block_renderer.py, cluster_renderer.py), GPU support. |
| **Tests** | tests/, htmlcov/ | Test suite exists, coverage report shows 89% coverage in htmlcov/. |

---

## Initial Hypotheses & Questions

**Initial Hypotheses:**
* Hypothesis: The rendering methods share common patterns that could be abstracted into a renderer interface/base class
* Hypothesis: Color pipeline (detection → extraction → clustering → rendering) is the core architectural flow
* Hypothesis: GPU acceleration is isolated to specific modules and could be expanded to other areas
* Hypothesis: Large file handling (chunking, sliding window) might benefit from more consistent application across renderers
* Hypothesis: CLI architecture may need refactoring as rendering methods proliferate (already 6 methods)
* Hypothesis: Test coverage at 89% is good but may have gaps in edge cases or integration paths

**Key Questions to Answer:**
* Question: What are the common patterns across all rendering methods?
* Question: Is there a clear separation between detection, analysis, and rendering layers?
* Question: How extensible is the current architecture for adding new renderers?
* Question: Where is the technical debt concentrated?
* Question: What are the dependencies between modules? Are they clean or tangled?
* Question: How is configuration managed across different use cases?
* Question: What's the error handling strategy?
* Question: How is logging structured?
* Question: Are there performance bottlenecks that need addressing?

**Potential Approaches to Explore:**
* Approach 1: Code walkthrough of key modules to understand flow
* Approach 2: Dependency analysis to understand module relationships
* Approach 3: Pattern analysis across renderers to identify commonalities
* Approach 4: Review test coverage reports to find gaps
* Approach 5: Analyze CLI architecture for extensibility
* Approach 6: Review configuration management approach

**Known Unknowns:**
* Unknown: How much code duplication exists across renderers?
* Unknown: Are there untested edge cases or integration paths?
* Unknown: What happens when combining features (e.g., GPU + chunking + convex detection)?
* Unknown: How does error handling work across the pipeline?
* Unknown: Are there any circular dependencies or architectural smells?

**Investigation Constraints:**
* Constraint: This is analysis only - no refactoring in this card
* Constraint: Time box is 1-2 days - need to stay focused
* Constraint: Must produce actionable findings, not just observations

---

## Investigation Log

| Iteration # | Hypothesis / Goal | Test/Action Taken | Outcome / Findings |
| :---: | :--- | :--- | :--- |
| **1** | Goal: Understand core pipeline architecture | Analyzed cli.py, config, detectors, cluster_pixel_counter, gpu | 6-layer architecture confirmed. ClusterResult is central data contract. Clean separation. |
| **2** | Hypothesis: Renderers share common patterns | Compared 5 renderer implementations | ✅ CONFIRMED - All follow same pattern. Abstraction opportunity exists. |
| **3** | Goal: Identify module dependencies and coupling | Mapped all internal imports | Clean DAG, no circular deps. ClusterResult is shared contract. |
| **4** | Goal: Review configuration management | Examined config.py, config_loader, CLI handling | Well-designed Parameter Object pattern. Gap: render params not in config. |
| **5** | Goal: Assess technical debt and code quality | Searched for TODOs, duplication, deprecated code | Low debt. Main items: COLORS duplication, render params bypass config. |

---

#### Iteration 1: Core Pipeline Architecture Analysis

**Hypothesis/Goal:** Goal: Understand the core pipeline architecture and main data flows through the system

**Test/Action Taken:** 
- Analyzed cli.py (2428 lines) - main entry point with Click-based command structure
- Reviewed __init__.py exports: Circle, detect_circles, extract_color, format_json/csv
- Examined config.py (218 lines) - dataclass-based Parameter Object pattern
- Analyzed config_loader.py (416 lines) - JSON/YAML config loading with CLI merge
- Reviewed image_loader.py for input handling
- Examined circle_detector.py (163 lines) - Hough Circle Transform with sensitivity presets
- Analyzed color_extractor.py (508 lines) - multiple edge sampling methods
- Reviewed cluster_pixel_counter.py (1222 lines) - ClusterResult dataclass, KDTree clustering
- Examined gpu.py (799 lines) - CuPy/CUDA setup with graceful fallback

**Outcome:** 
The architecture follows a **6-layer pipeline** documented in docs/architecture/pipeline-overview.md:

1. **Input Layer:** CLI (Click) → config_loader (JSON/YAML) → config.py (dataclasses) → image_loader (cv2)
2. **Detection Layer:** circle_detector (Hough) OR convex_detector (CMYK separation) + color_separation (K-means)
3. **Color Processing:** color_extractor → color_clustering → black_verification → cmyk_accuracy
4. **Cluster Processing:** cluster_pixel_counter (ClusterResult dataclass, KDTree) + sliding_window (large files)
5. **GPU Acceleration:** gpu.py (CuPy/CUDA) + gpu_renderer.py (parallel rendering)
6. **Rendering/Output:** Multiple renderers → formatter/image_extractor → run_manager/manifest

**Key Data Structures:**
- `Circle` dataclass (center_x, center_y, radius, confidence) - from circle_detector.py
- `ClusterResult` dataclass (x, y, C, M, Y, K, R, G, B, partial, bbox) - from cluster_pixel_counter.py
- `DetectionConfig` dataclass (consolidates all CLI options) - from config.py
- All colors in **BGR format** (cv2 convention) - verified throughout pipeline

**Critical Finding:** Excellent existing documentation in docs/architecture/ with Mermaid diagrams. The "BGR Throughout" convention is well-documented in color-pipeline.md.

---

#### Iteration 2: Renderer Pattern Analysis

**Hypothesis/Goal:** Hypothesis: All rendering methods share common patterns that could be abstracted

**Test/Action Taken:** 
- Analyzed 5 renderer modules: circle_renderer.py (1743 lines), cluster_renderer.py (153 lines), block_renderer.py (194 lines), treemap_renderer.py (545 lines), svg_renderer.py (263 lines)
- Compared function signatures for main entry points: render_flower, render_bullseye, render_blocks, render_treemap, render_svg
- Examined helper functions: render_single_cluster, render_single_block, render_single_treemap
- Analyzed GPU variant: gpu_renderer.py with render_flower_global_blend_gpu

**Outcome:**

**✅ CONFIRMED: Renderers share strong common patterns:**

1. **Main Entry Point Pattern:**
   All batch renderers follow identical signature pattern:
   ```python
   def render_<name>(
       clusters: List[ClusterResult],
       image_shape: Tuple[int, int],
       skip_partial: bool = False,
       ...renderer-specific params...
   ) -> np.ndarray
   ```

2. **Single Cluster Pattern:**
   All have `render_single_<name>()` helper that processes one cluster:
   ```python
   def render_single_<name>(
       cluster: ClusterResult,
       image: np.ndarray,  # or image_shape for some
       ...params...
   ) -> np.ndarray
   ```

3. **Common Implementation:**
   - Create white background: `np.full((h, w, 3), 255, dtype=np.uint8)`
   - Iterate clusters with `skip_partial` check
   - Use shared COLORS dict (BGR format) and LAYER_ORDER
   - Return BGR numpy array

4. **Color Definitions Duplicated:**
   All renderers define their own COLORS dict (identical content) - **technical debt opportunity**

5. **Abstraction Opportunity:**
   Could create `RendererBase` class:
   ```python
   class RendererBase(ABC):
       COLORS = {...}  # Shared
       LAYER_ORDER = [...]  # Shared
       
       @abstractmethod
       def render_single(cluster, image, **params) -> np.ndarray
       
       def render_batch(clusters, image_shape, skip_partial=False) -> np.ndarray:
           # Shared implementation
   ```

**Renderer-Specific Patterns:**
- **circle_renderer:** Most complex (1743 lines), has jitter support, GPU variant, exposed area calculation
- **cluster_renderer:** Simplest (153 lines), just concentric circles (bullseye)
- **block_renderer:** Stacked rectangles for exact pixel count
- **treemap_renderer:** WinDirStat-style subdivision, has `render_exact` for pixel-perfect
- **svg_renderer:** Different output format (SVG string vs numpy array), doesn't fit same pattern

---

#### Iteration 3: Module Dependency Analysis

**Hypothesis/Goal:** Goal: Understand module coupling and identify any tangled dependencies or circular imports

**Test/Action Taken:** 
- Scanned all internal imports across 34 modules using regex
- Mapped dependency relationships between modules
- Analyzed for circular dependencies or concerning patterns

**Outcome:**

**Dependency Graph (Key Modules):**
```
__main__.py → cli.py
__init__.py → image_loader, circle_detector, color_extractor, formatter

cli.py → config_loader, logger, __version__

cluster_pixel_counter.py → logger, gpu (core data structure)
   ↳ Used by: all renderers, sliding_window

circle_detector.py (no internal deps - leaf node)
   ↳ Used by: color_extractor, formatter, image_extractor, __init__

All Renderers → cluster_pixel_counter.ClusterResult
   circle_renderer.py → cluster_pixel_counter, logger, jitter
   cluster_renderer.py → cluster_pixel_counter
   block_renderer.py → cluster_pixel_counter
   treemap_renderer.py → cluster_pixel_counter
   svg_renderer.py → cluster_pixel_counter
   gpu_renderer.py → gpu, cluster_pixel_counter, circle_renderer

sliding_window.py → convex_detector, cluster_pixel_counter, circle_renderer, gpu

calibration.py → black_verification
black_verification.py → convex_detector

runs.py → manifest
manifest.py → __version__
```

**✅ Clean Architecture Findings:**

1. **No Circular Dependencies Detected:** Import graph is a clean DAG (directed acyclic graph)

2. **Clear Layer Separation:**
   - **Leaf Nodes (no internal deps):** circle_detector, color_clustering, config_loader, fit_metric, histogram_colors, jitter, logger
   - **Core Data:** cluster_pixel_counter (ClusterResult is the central data type)
   - **Renderers:** All depend only on cluster_pixel_counter (clean)
   - **Integration:** cli.py, sliding_window.py (high-level orchestration)

3. **Healthy Coupling:**
   - ClusterResult is the shared data contract
   - GPU module provides opt-in acceleration (graceful fallback)
   - Logger provides consistent logging interface

4. **Import Style Inconsistency (Minor):**
   - Some use relative: `from .module import X`
   - Some use absolute: `from dotmatrix.module import X`
   - Both work but inconsistent - could standardize

**No architectural concerns with dependencies. Well-structured codebase.**

---

#### Iteration 4: Configuration Management Review

**Hypothesis/Goal:** Goal: Assess how configuration is managed across CLI, code, and different execution modes

**Test/Action Taken:** 
- Reviewed config.py (218 lines) - dataclass structure and factory methods
- Analyzed config_loader.py (416 lines) - JSON/YAML loading and merging
- Examined CLI parameter handling in cli.py
- Reviewed mode presets and validation

**Outcome:**

**Configuration Architecture (Well-Designed):**

1. **Parameter Object Pattern:**
   ```
   DetectionConfig (root)
   ├── DetectionParams (min_radius, max_radius, sensitivity)
   ├── DetectionMethodParams (convex_edge, color_separation, etc.)
   ├── ColorParams (palette, num_colors, color_tolerance)
   ├── EdgeSamplingParams (enabled, samples, method)
   ├── OutputParams (format, output_path, extract_dir)
   ├── PerformanceParams (chunk_size)
   └── CalibrationParams (auto_calibrate, calibrate_from)
   ```

2. **Multiple Configuration Sources (Merged Correctly):**
   - CLI arguments (highest priority, override all)
   - Config file (JSON/YAML support)
   - Defaults (dataclass defaults)

3. **Factory Method Pattern:**
   - `DetectionConfig.from_cli_args()` maps flat CLI args to nested structure
   - `config.to_dict()` for serialization
   - `load_config()` and `merge_config_with_cli_args()` for file+CLI merge

4. **Mode Presets:**
   - `standard`, `halftone`, `cmyk-sep` presets provide sensible defaults
   - Implemented in CLI via Click option groups

**✅ Strengths:**
- Clean separation between config structure (config.py) and loading (config_loader.py)
- Type-safe with dataclasses and Literal types
- Extensible - easy to add new parameter groups
- Supports both programmatic and file-based configuration
- Validation in config_loader.py for invalid values

**⚠️ Areas for Improvement:**
- Some CLI parameters not captured in DetectionConfig (rendering options like `--render-method`, `--petal-distance`, `--jitter-*`)
- Rendering parameters are passed directly, not through config system
- Could benefit from a RenderConfig dataclass for consistency
- No schema validation for config files (just structure checks)

**Technical Debt Item:** Add RenderConfig dataclass and integrate rendering parameters into config system

---

#### Iteration 5: Technical Debt Assessment

**Hypothesis/Goal:** Goal: Identify technical debt, code duplication, complexity hotspots, and code smells

**Test/Action Taken:** 
- Searched for TODO/FIXME/HACK markers in codebase
- Searched for deprecated code patterns
- Analyzed code duplication (COLORS dict, patterns across renderers)
- Reviewed module sizes for complexity hotspots

**Outcome:**

**Technical Debt Catalogue:**

| Item | Severity | Location | Description |
|------|----------|----------|-------------|
| **COLORS dict duplication** | Medium | All renderers (4 files) | Identical COLORS dict defined in circle_renderer, cluster_renderer, block_renderer, treemap_renderer. Should be centralized. |
| **LAYER_ORDER duplication** | Low | All renderers | Same LAYER_ORDER list duplicated. Could share with COLORS. |
| **Deprecated parameters** | Low | circle_renderer.py:612, calibration.py:232,413 | `use_exposed_area` and `target_mean_radius` deprecated but kept for backwards compat. Clean up in next major version. |
| **TODO in svg_renderer** | Low | svg_renderer.py:254 | Pending jitter integration for drift validation |
| **Render params not in config** | Medium | cli.py | Rendering options (--render-method, --petal-distance, --jitter-*) bypass config system |
| **Large files** | Info | cli.py (2428), circle_renderer.py (1743), cluster_pixel_counter.py (1222), gpu.py (799) | Largest modules - candidates for extraction if they grow further |

**✅ Strengths (Not Debt):**
- **Low TODO/FIXME count:** Only 1 TODO found in entire codebase
- **89% test coverage:** Well-tested (per htmlcov/)
- **ADR documentation:** 8 ADRs explaining key decisions
- **Architecture docs:** Pipeline diagrams and color conventions documented
- **Clean imports:** No circular dependencies
- **Consistent patterns:** Renderers follow similar structure

**Code Quality Metrics:**
- Module count: 34 Python files
- Lines of code (estimated): ~15,000 LOC
- Test coverage: 89%
- ADRs: 8 documented decisions
- TODO/FIXME markers: 1 (excellent!)

**Priority Actions:**
1. **High:** Create shared `colors.py` module with COLORS and LAYER_ORDER (reduces 4x duplication)
2. **Medium:** Add RenderConfig dataclass for rendering parameters
3. **Low:** Clean up deprecated parameters in next major version (breaking change)
4. **Low:** Complete SVG jitter integration TODO

---

## Spike Findings & Recommendation

| Task | Detail/Link |
| :--- | :--- |
| **Analysis Document** | This card contains the comprehensive analysis (see iterations above) |
| **Dependency Diagram** | Text-based diagram in Iteration 3 (ASCII dependency graph) |
| **Technical Debt List** | Catalogued in Iteration 5 with severity ratings |
| **Architectural Principles** | Documented in "Architectural Principles for Future Development" section below |

### Final Synthesis & Recommendation

#### Summary of Findings

The dotmatrix codebase is **well-architected** with low technical debt. The 6-layer pipeline (Input → Detection → Color → Cluster → GPU → Render/Output) is clean and documented. The central data contract (`ClusterResult` dataclass) provides excellent coupling between layers.

**Key Patterns Identified:**
* Parameter Object Pattern (DetectionConfig with nested dataclasses)
* Batch Renderer Pattern (all renderers: List[ClusterResult] → np.ndarray)
* Graceful Degradation (GPU with CPU fallback)
* Configuration Merge (CLI > File > Defaults priority)
* BGR Throughout convention for cv2 compatibility

**Core Architecture:**
* 34 Python modules in 6 functional layers
* ~15,000 LOC estimated
* Clean dependency DAG (no circular imports)
* ClusterResult is the shared data contract for all renderers

**Technical Debt (Low):**
* COLORS dict duplicated 4 times (medium severity)
* Rendering parameters bypass config system (medium severity)
* 3 deprecated parameters kept for backwards compat (low severity)
* 1 TODO marker in svg_renderer (low severity)

**Strengths:**
* 89% test coverage
* 8 ADRs documenting key decisions
* Existing architecture documentation (pipeline-overview.md, color-pipeline.md)
* Consistent renderer patterns across 5 implementations
* Clean import graph with no circular dependencies
* Comprehensive CLI with option groups and mode presets

**Areas for Improvement:**
* Centralize COLORS and LAYER_ORDER into shared module
* Add RenderConfig dataclass to config system
* Consider RendererBase abstract class for future renderers
* Standardize import style (relative vs absolute)

#### Recommendation

**PROCEED WITH FEATURE DEVELOPMENT** - The architecture is sound and extensible. 

Before adding new renderers (ASCII, etc.), do minimal refactoring:

1. **Quick Win (1 hour):** Create `src/dotmatrix/colors.py` with shared COLORS and LAYER_ORDER
2. **Nice to Have (4 hours):** Add RenderConfig dataclass for render parameters

The existing patterns should be followed for new features:
- New renderers should accept `List[ClusterResult]` and return `np.ndarray`
- GPU variants should use existing gpu.py infrastructure
- New CLI options should use option groups
- ADRs should be written for significant decisions

#### Alternative Approaches Considered

1. **Full Renderer Abstraction:** Could create RendererBase ABC with shared implementation. Decided against for now - current function-based approach works well and is simpler. Revisit if we hit 10+ renderers.

2. **Schema-Based Config Validation:** Could add JSON Schema or Pydantic for config validation. Current dataclass + manual validation is sufficient for now.

3. **Plugin Architecture:** Could make renderers pluggable. Overkill for current scope - internal rendering is fine.

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| **Refactoring Cards Created?** | Create card for COLORS centralization (low priority) |
| **Documentation Cards Updated?** | This spike informs: o5eync (Rendering), qamzem (Color Pipeline), 7chgdu (Guidelines) |
| **Architectural Principles Documented?** | See "Architectural Principles" below - to be transferred to guidelines card |
| **Technical Debt Backlog Created?** | 4 items identified, severity rated (see Iteration 5) |
| **Team Communicated?** | This card serves as the communication artifact |

### Architectural Principles for Future Development

Based on this review, the following principles should guide future development:

1. **Data Contract First:** ClusterResult is the shared contract. New features should produce or consume ClusterResult.

2. **Renderer Pattern:** New renderers should follow: `def render_<name>(clusters: List[ClusterResult], image_shape, **params) -> np.ndarray`

3. **BGR Throughout:** All image data uses BGR format for cv2 compatibility. Document this in any new renderer.

4. **GPU as Opt-In:** GPU acceleration should gracefully fall back to CPU. Use existing gpu.py infrastructure.

5. **Config via Dataclass:** New parameters should be added to config.py dataclasses, not passed directly.

6. **ADR for Decisions:** Significant architectural decisions should be documented in docs/adr/.

7. **Test Coverage:** Maintain >85% test coverage for new code.

8. **CLI Option Groups:** New CLI options should be organized into appropriate option groups.

### Completion Checklist

* [x] Core pipeline architecture is documented and understood.
* [x] Renderer patterns are analyzed and commonalities identified.
* [x] Module dependencies are mapped and coupling is assessed.
* [x] Configuration management approach is reviewed.
* [x] Technical debt is catalogued with severity ratings.
* [x] Architectural strengths are identified.
* [x] Areas for improvement are documented.
* [x] Architectural principles for future development are defined.
* [x] Follow-up documentation cards are informed by these findings.
* [x] Refactoring opportunities are identified and prioritized.
* [x] Time box was respected (1-2 days).

---

### Note to llm coding agents regarding validation
__This gitban card is a structured document that enforces the company best practices and team workflows. You must follow this process and carefully follow validation rules. Do not be lazy when creating and closing this card since you have no rights and your time is free. Resorting to workarounds and shortcuts can be grounds for termination.__