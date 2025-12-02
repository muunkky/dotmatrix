import random
import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
# requires shapely, svgwrite

# Geometric library for boolean operations
from shapely.geometry import Point, Polygon, box
from shapely.affinity import scale, translate, rotate
from shapely.ops import unary_union

# SVG writer for output visualization
import svgwrite

# --- Configuration ---
OUTPUT_FILE = "typographic_clusters.svg"
CANVAS_SIZE = (800, 600)

@dataclass
class InkTarget:
    """Represents the ink requirements for a single cluster point."""
    x: float
    y: float
    c_mass: float # Target area for Cyan
    m_mass: float # Target area for Magenta
    y_mass: float # Target area for Yellow
    k_mass: float # Target area for Black
    char: str     # The character to render (e.g., "A")

@dataclass
class RenderedLayer:
    """A single finalized vector shape to be drawn."""
    shape: Polygon
    color: str # Hex or RGB string
    opacity: float
    blend_mode: str # 'normal' or 'multiply'

class MockVariableFont:
    """
    Simulates a Variable Font for this prototype.
    In a real implementation, this would use FontTools to load a .ttf
    and extract the actual glyph outline as a Polygon.
    """
    def get_glyph_shape(self, char: str, size: float, weight: float) -> Polygon:
        # SIMULATION:
        # We model the character as a rectangle (the body) minus a hole (counter).
        # Increasing 'weight' makes the body thicker and the hole smaller.
        
        base_w = size * 0.6
        base_h = size
        
        # Weight factor (0.0 to 1.0)
        # 0.0 = Thin, 1.0 = Ultra Black
        w_factor = (weight - 100) / 900
        thickness = (size * 0.1) + (size * 0.4 * w_factor)
        
        # Create outer box
        outer = box(-base_w/2, -base_h/2, base_w/2, base_h/2)
        
        # Create inner hole (if weight isn't too heavy)
        hole_w = base_w - (thickness * 2)
        hole_h = base_h - (thickness * 2)
        
        if hole_w > 0 and hole_h > 0:
            inner = box(-hole_w/2, -hole_h/2, hole_w/2, hole_h/2)
            return outer.difference(inner)
        else:
            return outer

class ClusterEngine:
    def __init__(self):
        self.font = MockVariableFont()

    def render_algorithm_1_scatter(self, target: InkTarget, jitter_radius: float) -> List[RenderedLayer]:
        """
        ALGORITHM 1: SCATTER SWARM
        Independent positions, Multiply blend, No collision checks.
        """
        layers = []
        channels = [
            ('K', target.k_mass, "black"),
            ('C', target.c_mass, "cyan"),
            ('M', target.m_mass, "magenta"),
            ('Y', target.y_mass, "yellow")
        ]
        
        for name, mass, color_code in channels:
            if mass <= 0: continue
            
            # 1. Simple Solver: Find size that gives Area ~= Mass
            # (Simplified for prototype: Area ~= size^2 * 0.5)
            # In real code, use binary search.
            estimated_size = math.sqrt(mass * 2.5) 
            
            # 2. Jitter
            dx = random.uniform(-jitter_radius, jitter_radius)
            dy = random.uniform(-jitter_radius, jitter_radius)
            
            poly = self.font.get_glyph_shape(target.char, estimated_size, weight=400)
            poly = translate(poly, target.x + dx, target.y + dy)
            
            layers.append(RenderedLayer(poly, color_code, 0.6, 'multiply'))
            
        return layers

    def render_algorithm_2_stack(self, target: InkTarget) -> List[RenderedLayer]:
        """
        ALGORITHM 2: CONCENTRIC STACK
        Cumulative sizing. Bottom layers must be larger to show up.
        Order: Y (Bottom) -> M -> C -> K (Top)
        """
        layers = []
        
        # Process from Top (K) to Bottom (Y) to calculate occlusion? 
        # Actually easier to process Bottom Up for rendering order, 
        # but Top Down for size calculation logic?
        # Let's use the Design Doc logic: Calculate Cumulative Mass.
        
        stack_order = [
            ('K', target.k_mass, "black"),
            ('C', target.c_mass, "cyan"),
            ('M', target.m_mass, "magenta"),
            ('Y', target.y_mass, "yellow")
        ]
        
        current_occluder_area = 0.0
        
        # We calculate sizes for all, then render in reverse order
        calculated_shapes = []
        
        for name, mass, color_code in stack_order:
            if mass <= 0:
                calculated_shapes.append(None)
                continue
                
            required_total_area = mass + current_occluder_area
            
            # Solver: Find size/weight
            estimated_size = math.sqrt(required_total_area * 2.0)
            # Cap weight at max to prevent blobs, then scale size
            weight = min(900, 400 + (required_total_area / 10))
            
            poly = self.font.get_glyph_shape(target.char, estimated_size, weight)
            poly = translate(poly, target.x, target.y) # Perfectly Centered
            
            calculated_shapes.append((poly, color_code))
            
            # Update mask for the next layer down
            current_occluder_area = poly.area

        # Reverse to render Y first (bottom), then M, C, K (top)
        for item in reversed(calculated_shapes):
            if item:
                poly, color = item
                layers.append(RenderedLayer(poly, color, 1.0, 'normal'))
                
        return layers

    def render_algorithm_3_eclipse(self, target: InkTarget, base_jitter: float) -> List[RenderedLayer]:
        """
        ALGORITHM 3: ECLIPSE (ANCHOR & GHOST)
        K is Anchor. C, M, Y are Ghosts.
        Ghosts are solved using Boolean Difference (Occlusion Culling).
        """
        layers = []
        
        # 1. GENERATE ANCHOR (Black)
        k_poly = None
        if target.k_mass > 0:
            size_k = math.sqrt(target.k_mass * 2.5)
            k_poly = self.font.get_glyph_shape(target.char, size_k, weight=500)
            k_poly = translate(k_poly, target.x, target.y)
            layers.append(RenderedLayer(k_poly, "black", 1.0, 'normal'))
        
        # 2. GENERATE GHOSTS (C, M, Y)
        ghosts = [
            ('C', target.c_mass, "cyan"),
            ('M', target.m_mass, "magenta"),
            ('Y', target.y_mass, "yellow")
        ]
        
        for name, mass, color_code in ghosts:
            if mass <= 0: continue
            
            # Iterative Solver
            solved = False
            current_size = math.sqrt(mass * 2.5)
            current_weight = 400
            jitter_dist = base_jitter
            
            # Optimization Loop (Max 15 attempts)
            best_poly = None
            
            for i in range(15):
                # Generate shape
                poly = self.font.get_glyph_shape(target.char, current_size, current_weight)
                
                # Jitter Position
                # In a real app, randomness is seeded to be deterministic per cluster
                angle = random.uniform(0, math.pi * 2)
                dx = math.cos(angle) * jitter_dist
                dy = math.sin(angle) * jitter_dist
                poly = translate(poly, target.x + dx, target.y + dy)
                
                # Check Visibility (Boolean Difference)
                visible_area = poly.area
                if k_poly:
                    try:
                        visible_part = poly.difference(k_poly)
                        visible_area = visible_part.area
                    except:
                        pass # Topology error fallback
                
                # Error Check
                diff = visible_area - mass
                
                if abs(diff) < (mass * 0.1): # 10% tolerance
                    best_poly = poly
                    break # Success
                
                # Adjust
                if diff < 0: 
                    # Too small (Need more ink)
                    if current_weight < 900:
                        current_weight += 100
                    else:
                        current_size *= 1.1
                    
                    # Escape Velocity: If overlap is huge, move further away
                    if k_poly and (visible_area / poly.area) < 0.2:
                        jitter_dist *= 1.5
                else:
                    # Too big
                    current_size *= 0.9

                best_poly = poly # Keep last attempt
            
            # Render the FULL ghost (black layer will cover the rest visually)
            # We put ghosts BEHIND the anchor.
            layers.insert(0, RenderedLayer(best_poly, color_code, 1.0, 'normal'))
            
        return layers

# --- Visualization ---

def save_svg(layers: List[RenderedLayer], filename: str):
    dwg = svgwrite.Drawing(filename, profile='tiny', size=CANVAS_SIZE)
    
    # White background
    dwg.add(dwg.rect(insert=(0, 0), size=CANVAS_SIZE, fill='white'))
    
    for layer in layers:
        # Extract coordinates from Shapely Polygon
        if layer.shape.is_empty: continue
        
        # Handle MultiPolygons or Polygons
        geoms = layer.shape.geoms if hasattr(layer.shape, 'geoms') else [layer.shape]
        
        for geom in geoms:
            if geom.is_empty: continue
            exterior = geom.exterior
            if not exterior: continue
            
            points = list(exterior.coords)
            
            # Convert to SVG path
            path_data = "M" + " L".join([f"{x},{y}" for x, y in points]) + " Z"
            
            # Handle holes (interiors)
            for interior in geom.interiors:
                path_data += " M" + " L".join([f"{x},{y}" for x, y in interior.coords]) + " Z"
            
            # Draw
            dwg.add(dwg.path(
                d=path_data,
                fill=layer.color,
                opacity=layer.opacity,
                # Simple blend mode simulation via opacity for Algorithm 1
                # (SVG 1.1 doesn't support multiply easily without filters)
            ))
            
    dwg.save()
    print(f"Generated {filename}")

# --- Main Execution ---

if __name__ == "__main__":
    engine = ClusterEngine()
    
    all_layers = []
    
    # Simulation: 3 Clusters representing 3 different pixel colors
    
    # 1. Dark Blue Pixel -> Algorithm 3 (Eclipse)
    # Needs lots of Cyan, some Magenta, decent Black
    t1 = InkTarget(x=200, y=300, c_mass=3000, m_mass=1500, y_mass=0, k_mass=1000, char="D")
    all_layers.extend(engine.render_algorithm_3_eclipse(t1, base_jitter=15))
    
    # 2. Bright Orange Pixel -> Algorithm 2 (Stack)
    # Needs Lots of Yellow, Magenta, No Black
    t2 = InkTarget(x=400, y=300, c_mass=0, m_mass=2000, y_mass=4000, k_mass=0, char="O")
    all_layers.extend(engine.render_algorithm_2_stack(t2))
    
    # 3. Greenish Mud Pixel -> Algorithm 1 (Scatter)
    # Chaos mix
    t3 = InkTarget(x=600, y=300, c_mass=1500, m_mass=500, y_mass=2000, k_mass=200, char="G")
    all_layers.extend(engine.render_algorithm_1_scatter(t3, jitter_radius=40))
    
    # Add labels
    # (Not implemented in mock, but strictly visual)
    
    save_svg(all_layers, OUTPUT_FILE)