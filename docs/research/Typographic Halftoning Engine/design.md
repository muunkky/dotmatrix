# **Design Specification: Typographic Halftoning Engine**

## **1\. Overview**

This system reconstructs source images using "clusters" of text. Unlike traditional ASCII art, this engine treats text as physical "Ink Mass." The goal is to match the pixel density of the source image's CMYK/RGB channels by manipulating the Size, Weight, and Position of variable font characters.

## **2\. Core Definitions**

### **2.1 The Ink Mass Constraint**

The fundamental rule of the engine:

$$\\text{Area}(\\text{Glyph}\_{visible}) \\approx \\text{Target Mass}$$

Where "Target Mass" is the number of pixels of a specific color required in a specific region.

### **2.2 The Coordinate System**

* **Global Space:** The full dimensions of the print (e.g., 24" x 36").  
* **Cluster Space:** A local coordinate system relative to the center $(0,0)$ of a specific "pixel" or "dot" from the source image.

## **3\. Algorithm Specifications**

### **Algorithm A: The "Scatter Swarm" (Stochastic Jitter)**

Goal: High-energy, organic, "Pointillist" aesthetic.  
Logic:

1. **Independent Calculation:** Calculate the required scale for C, M, Y, and K independently based on their target mass.  
2. **Radial Jitter:** For each color channel, generate a random offset vector $(dx, dy)$ within a maximum radius $R$.  
3. **Blend Mode:** Render all layers with Multiply blending.  
4. **No Collision Detection:** Shapes are allowed to overlap freely. This creates "accidental" secondary colors (Red, Green, Blue).

### **Algorithm B: The "Concentric Stack" (Vertical Z-Index)**

Goal: High legibility, retro "Bullseye" aesthetic.  
Logic:

1. **Strict Ordering:** Layers are stacked vertically. Standard order: Black (Top) $\\to$ Cyan $\\to$ Magenta $\\to$ Yellow (Bottom).  
2. Cumulative Sizing (The Donut Logic):  
   To ensure a bottom layer (e.g., Yellow) provides $Y$ visible pixels, it must be larger than the layers above it.  
   $$\\text{Size}\_{Y} \= \\text{Function}(\\text{Target}\_{Y} \+ \\text{Area}\_{Magenta} \+ \\text{Area}\_{Cyan} \+ \\text{Area}\_{Black})$$  
3. **Centering:** All layers are perfectly centered at $(0,0)$.

### **Algorithm C: The "Eclipse" (Occlusion Culling)**

Goal: Professional Offset Print aesthetic. "Floating" colors anchored by crisp black text.  
Logic:

1. **The Anchor:** The Black (K) layer is calculated first. It is placed at $(0,0)$ and sized purely on $K$ mass.  
2. **The Ghosts:** C, M, and Y layers are offset (jittered).  
3. Boolean Subtraction Loop:  
   For each color:  
   * Generate Shape $S$.  
   * Subtract the Black Anchor: $S\_{visible} \= S \- S\_{anchor}$.  
   * Measure $\\text{Area}(S\_{visible})$.  
   * **Feedback:**  
     * If $\\text{Area} \< \\text{Target}$: Increase Scale/Weight.  
     * **Escape Velocity:** If Scale is maxed out and Area is still low (total occlusion), increase Jitter Distance to move the shape out from behind the anchor.  
     * If $\\text{Area} \> \\text{Target}$: Decrease Scale/Weight.

## **4\. Technical Architecture**

### **4.1 Dependency Stack**

* **Shapely:** Required for robust boolean operations (intersection, difference). Raster approaches (counting pixels) are too slow and resolution-dependent for large format print.  
* **FontTools:** For extracting glyph paths from Variable Fonts (.ttf) and instantiating specific axes (wght, wdth).  
* **SVG/Cairo:** Vector output format is mandatory to preserve print resolution.

### **4.2 Data Structures**

**InkCluster Object:**

* position: (x, y)  
* targets: { 'C': 500, 'M': 120, 'Y': 0, 'K': 800 }  
* char: "A"

**RenderPass Object:**

* poly: Shapely Polygon  
* color: (C, M, Y, K) tuple  
* z\_index: int