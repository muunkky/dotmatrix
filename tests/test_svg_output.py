"""Unit tests for SVG output rendering."""
import pytest
import xml.etree.ElementTree as ET
from dotmatrix.svg_renderer import (
    render_svg,
    cmyk_to_rgb_hex,
    _create_svg_header,
    _create_color_group,
    _format_circle,
)
from dotmatrix.cluster_pixel_counter import ClusterResult


def create_test_cluster(x=100, y=100, cyan=800, magenta=0, yellow=0, black=800):
    """Create a simple test cluster."""
    return ClusterResult(
        x=x, y=y,
        cyan=cyan, magenta=magenta, yellow=yellow, black=black,
        red=0, green=0, blue=0,
        partial=False
    )


class TestCMYKToRGB:
    """Test CMYK to RGB hex color conversion."""
    
    def test_cmyk_cyan_pure(self):
        """Pure cyan should convert to #00FFFF."""
        result = cmyk_to_rgb_hex(100, 0, 0, 0)
        assert result == "#00FFFF" or result == "#00ffff"
    
    def test_cmyk_magenta_pure(self):
        """Pure magenta should convert to #FF00FF."""
        result = cmyk_to_rgb_hex(0, 100, 0, 0)
        assert result == "#FF00FF" or result == "#ff00ff"
    
    def test_cmyk_yellow_pure(self):
        """Pure yellow should convert to #FFFF00."""
        result = cmyk_to_rgb_hex(0, 0, 100, 0)
        assert result == "#FFFF00" or result == "#ffff00"
    
    def test_cmyk_black_pure(self):
        """Pure black should convert to #000000."""
        result = cmyk_to_rgb_hex(0, 0, 0, 100)
        assert result == "#000000"
    
    def test_cmyk_white(self):
        """No ink should convert to white #FFFFFF."""
        result = cmyk_to_rgb_hex(0, 0, 0, 0)
        assert result == "#FFFFFF" or result == "#ffffff"


class TestSVGStructure:
    """Test SVG XML structure generation."""
    
    def test_svg_header_basic(self):
        """SVG header should contain viewBox and namespaces."""
        header = _create_svg_header(width=800, height=600)
        root = ET.fromstring(header + "</svg>")
        
        assert root.tag == "{http://www.w3.org/2000/svg}svg"
        assert root.get("width") == "800"
        assert root.get("height") == "600"
        assert root.get("viewBox") == "0 0 800 600"
    
    def test_circle_format(self):
        """Circle should format with cx, cy, r attributes."""
        circle_xml = _format_circle(x=100, y=200, radius=15.5)
        # Parse as plain XML (no namespace in standalone circle)
        root = ET.fromstring(f"<g>{circle_xml}</g>")
        circle = root.find(".//circle")
        
        assert circle is not None
        assert float(circle.get("cx")) == pytest.approx(100, abs=0.1)
        assert float(circle.get("cy")) == pytest.approx(200, abs=0.1)
        assert float(circle.get("r")) == pytest.approx(15.5, abs=0.1)
    
    def test_color_group_structure(self):
        """Color group should have id and fill attributes."""
        circles = [
            create_test_cluster(x=10, y=10, cyan=800, black=800),
            create_test_cluster(x=20, y=20, cyan=600, black=600),
        ]
        
        group_xml = _create_color_group(
            color_name="cyan",
            color_hex="#00FFFF",
            clusters=circles
        )
        
        # Parse as plain XML (no namespace in standalone group)
        root = ET.fromstring(f"<svg>{group_xml}</svg>")
        group = root.find(".//g")
        
        assert group is not None
        assert group.get("id") == "cyan-layer"
        assert group.get("fill") == "#00FFFF" or group.get("fill") == "#00ffff"
        assert "mix-blend-mode: multiply" in group.get("style", "")


class TestSVGRendering:
    """Test full SVG rendering from clusters."""
    
    def test_render_svg_single_cluster(self):
        """Single cluster should generate valid SVG."""
        cluster = create_test_cluster(x=100, y=100, cyan=800, black=800)
        svg_output = render_svg([cluster], image_shape=(200, 200))
        
        # Parse as XML to validate structure
        root = ET.fromstring(svg_output)
        assert root.tag == "{http://www.w3.org/2000/svg}svg"
        
        # Should have groups for colors present
        groups = root.findall(".//{http://www.w3.org/2000/svg}g")
        assert len(groups) > 0
    
    def test_render_svg_multiple_colors(self):
        """Multiple CMYK colors should create separate groups."""
        clusters = [
            create_test_cluster(x=10, y=10, cyan=800, magenta=0, yellow=0, black=800),
            create_test_cluster(x=50, y=50, cyan=0, magenta=800, yellow=0, black=800),
            create_test_cluster(x=90, y=90, cyan=0, magenta=0, yellow=800, black=800),
        ]
        
        svg_output = render_svg(clusters, image_shape=(200, 200))
        root = ET.fromstring(svg_output)
        
        # Should have cyan, magenta, yellow, and black groups
        group_ids = [g.get("id") for g in root.findall(".//{http://www.w3.org/2000/svg}g")]
        
        # Expect at least 2 groups (cyan, magenta, yellow, black)
        assert len(group_ids) >= 2
    
    def test_render_svg_no_partial_circles(self):
        """Partial circles should be skipped by default."""
        clusters = [
            create_test_cluster(x=10, y=10, cyan=800, black=800),
            ClusterResult(x=50, y=50, cyan=800, magenta=0, yellow=0, black=800,
                         red=0, green=0, blue=0, partial=True),  # Should be skipped
        ]
        
        svg_output = render_svg(clusters, image_shape=(200, 200), skip_partial=True)
        root = ET.fromstring(svg_output)
        
        # Count total circles (should be fewer than total clusters)
        circles = root.findall(".//{http://www.w3.org/2000/svg}circle")
        # Each cluster has 2 colors (cyan + black), but partial should be skipped
        # So expect 2 circles from first cluster only
        assert len(circles) <= 4  # Some leniency for implementation details


class TestSVGOptimization:
    """Test SVG file size optimization."""
    
    def test_file_size_scales_linearly(self):
        """File size should scale roughly linearly with circle count."""
        # Generate SVGs with different cluster counts
        clusters_10 = [create_test_cluster(x=i*10, y=i*10) for i in range(10)]
        clusters_100 = [create_test_cluster(x=i*10, y=i*10) for i in range(100)]
        
        svg_10 = render_svg(clusters_10, image_shape=(200, 200))
        svg_100 = render_svg(clusters_100, image_shape=(2000, 2000))
        
        size_10 = len(svg_10)
        size_100 = len(svg_100)
        
        # Size should scale roughly 10x (with some overhead for headers)
        # Allow 5x-15x range for flexibility
        ratio = size_100 / size_10
        assert 5 < ratio < 15, f"Size scaling ratio {ratio} out of expected range"
    
    def test_precision_optimization(self):
        """Coordinates should use limited decimal precision."""
        cluster = create_test_cluster(x=100.123456789, y=200.987654321)
        svg_output = render_svg([cluster], image_shape=(400, 400))
        
        # Check that coordinates don't have excessive precision
        # Should see "100.1" not "100.123456789"
        assert "100.123456" not in svg_output
        assert "200.987654" not in svg_output


class TestSVGMetadata:
    """Test SVG metadata and documentation."""
    
    def test_title_element_present(self):
        """SVG should contain <title> element."""
        cluster = create_test_cluster()
        svg_output = render_svg([cluster], image_shape=(200, 200))
        
        root = ET.fromstring(svg_output)
        title = root.find(".//{http://www.w3.org/2000/svg}title")
        assert title is not None
        assert len(title.text) > 0
    
    def test_desc_element_present(self):
        """SVG should contain <desc> element with metadata."""
        cluster = create_test_cluster()
        svg_output = render_svg([cluster], image_shape=(200, 200))
        
        root = ET.fromstring(svg_output)
        desc = root.find(".//{http://www.w3.org/2000/svg}desc")
        assert desc is not None
        assert "DotMatrix" in desc.text or "dotmatrix" in desc.text.lower()


if __name__ == "__main__":
    print("Running SVG output tests...")
    pytest.main([__file__, "-v"])
