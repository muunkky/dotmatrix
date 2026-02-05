# Technical Proposal: Typographic Mosaic Rendering (Project "Text-Image")

## 1. Executive Summary

This proposal outlines the technical architecture for generating a visual image comprised entirely of running text. By mapping specific CMYK color data from source image clusters to individual text characters (glyphs), we create a macro-image visible from a distance while preserving micro-legibility of the text.

To solve the fundamental physical limitation of typography (low surface area/density), this proposal recommends a **Hybrid Rendering Engine**. This engine combines Ink Density Compensation (for the text) with a Background Halftone System (dots) to manage dynamic range, ensuring the final image is neither washed out nor muddy.

## 2. Core Concepts

| Term | Definition |
|------|------------|
| **Source Cluster** | A specific block of the source image re-sampled to match the aspect ratio of the target font. |
| **Target Glyph** | The specific character from the text story. |
| **Ink Ratio ($R_{ink}$)** | The percentage of surface area a specific glyph occupies within its bounding box (e.g., 'i' is ~15%, 'M' is ~45%). |
| **Ghost Factor** | A configurable density ceiling (e.g., 0.6) that prevents the algorithm from attempting to drive thin text to 100% black, which would result in clipping. |

## 3. System Architecture

The rendering pipeline consists of three distinct phases: Geometric Mapping, Logic Branching, and Compositing.

### Phase 1: Geometric Mapping (Pre-Processing)

Text naturally flows left-to-right, top-to-bottom, and letters are rarely perfect squares. To prevent image distortion, the source image must be re-mapped before color analysis.

1. **Font Analysis:** Determine the Aspect Ratio ($AR$) of the chosen font's bounding box (e.g., Courier New $\approx 0.6$).
2. **Grid Generation:** Divide the source image into rectangular cells of size $W \times (W / AR)$.
3. **Data Extraction:** For each cell, extract the average CMYK values.

### Phase 2: The Logic Branch (The Hybrid Engine)

The engine analyzes each cluster's properties (Saturation vs. Luminance) to choose the optimal rendering strategy.

#### Scenario A: High Contrast / Detail (The "K-Split")

- **Trigger:** Cluster has high Black ($K$) content or low Saturation.
- **Strategy:** Isolate Luminance to the background and Chroma to the text.
  - **Layer 1 (Background):** Black Halftone Dot. Size is driven by $K$.
  - **Layer 2 (Foreground):** Text carries the $C, M, Y$ data.

#### Scenario B: High Saturation (The "Component Mix")

- **Trigger:** Cluster is vibrant (e.g., bright Green, pure Red).
- **Strategy:** Split Primary and Secondary colors to maximize optical mixing.
  - **Layer 1 (Background):** Colored Dot (Primary channel, e.g., Cyan).
  - **Layer 2 (Foreground):** Colored Text (Secondary channel, e.g., Yellow).
- **Handling:** Standard layering is sufficient. Since the text sits on top of the dot, the colors naturally mix (visually or via overprint) to create the secondary color (e.g., Green) without requiring complex culling.

#### Scenario C: "Eclipse Mode" (Text-on-Text)

- **Trigger:** Specific aesthetic requirement where the K-layer is rendered as Black Text (using the Variable Font "Weight" axis) rather than a Dot, to match the style of the foreground story.
- **Strategy:**
  - **Layer 1 (Background):** Large, Heavy Black Text Character.
  - **Layer 2 (Foreground):** Colored Text Character (shifted or centered).
- **Advanced Handling (Occlusion Culling):** Required here. Because placing colored text on top of black text results in muddy/invisible glyphs, we must geometrically subtract the foreground shape from the background black glyph ("Knockout"). This ensures the colored text is legible against the dense black anchor.

### Phase 3: Compositing & Math

Once the strategy is chosen, we calculate the final render values.

#### 1. The Ink Density Formula

We must boost the color of the text because thin lines appear lighter than solid blocks.

$$C_{final} = \min\left(100\%, \frac{C_{source} \times \text{GhostFactor}}{R_{ink}} \right)$$

Where:
- $C_{final}$: The color applied to the text.
- $C_{source}$: The target color from the image.
- $R_{ink}$: The surface area of the specific letter being typed.
- **GhostFactor**: A scalar (0.0 - 1.0) representing the maximum achievable visual density.

#### 2. Variable Font Axis Manipulation

To increase the dynamic range of $R_{ink}$, we utilize Variable Fonts rather than standard weights.

- **Mechanism:** Map the target density directly to the `wght` (Weight) and `wdth` (Width) axes.
- **Formula:** `FontWeight = BaseWeight + (TargetDensity * WeightScalar)`
- **Result:** Darker image regions generate physically thicker glyphs (e.g., weight 800), while lighter regions use thinner glyphs (e.g., weight 200). This provides smooth gradients without needing extreme "Ghost Factor" compensation.

#### 3. The Halftone Dot Formula

The background dot fills the empty space left by the text (used in Scenarios A & B).

$$Radius = \sqrt{ \frac{K_{source}}{100} } \times \frac{\text{CellWidth}}{2}$$

## 4. Rendering Targets

The system must support two distinct output modes with different technical requirements.

### A. Web (CSS/Canvas) → RGB Simulation

For screen display, we simulate the ink interactions using CSS and DOM elements.

| Component | Implementation |
|-----------|----------------|
| **Structure** | A single `<div>` or `<span>` per character. |
| **Background** | `background-image: radial-gradient(...)` handles the Halftone Dot. |
| **Foreground** | `color: rgb(...)` handles the Text. |
| **Variable Fonts** | Use `font-variation-settings: 'wght' 700, 'wdth' 100`. |

### B. Print (PDF) → CMYK Fidelity

For physical production, we generate a PDF using ReportLab or similar tools.

| Component | Implementation |
|-----------|----------------|
| **Color Space** | Native CMYK (0.0-1.0 floats). |
| **Overprint Settings** | **Standard (Scenarios A & B):** Text object set to `Overprint: True`. |
| | **Eclipse Mode (Scenario C):** Explicit vector subtraction (culling) required in the PDF stream to create the knockout. |

## 5. Implementation Roadmap

| Version | Features |
|---------|----------|
| **MVP** | Monospaced font support, "K-Split" strategy only, Web Output. |
| **V2** (Advanced Typography) | Implement Variable Font Support (`fontTools` integration) to dynamically scale `wght` based on density. |
| **V3** (High-Contrast Handling) | Implement Occlusion Culling specifically for "Eclipse Mode" (Text-on-Black-Text) scenarios. |
| **V4** | PDF Generation with Overprint support. |