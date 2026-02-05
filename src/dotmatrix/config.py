"""Configuration dataclasses for DotMatrix detection parameters.

These dataclasses serve as Parameter Objects to consolidate the many CLI
options into structured, type-safe configuration objects.
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Literal


@dataclass
class DetectionParams:
    """Circle detection parameters."""
    min_radius: int = 1
    max_radius: int = 500
    min_distance: int = 20
    sensitivity: Literal['strict', 'normal', 'relaxed'] = 'normal'
    min_confidence: Optional[int] = None


@dataclass
class DetectionMethodParams:
    """Detection algorithm selection."""
    convex_edge: bool = False
    color_separation: bool = False
    use_histogram: bool = False
    sensitive_occlusion: bool = False
    morph_enhance: bool = False


@dataclass
class ColorParams:
    """Color detection and grouping parameters."""
    palette: str = 'cmyk'
    num_colors: int = 6
    color_tolerance: int = 20
    max_colors: Optional[int] = None
    exclude_background: bool = False


@dataclass
class EdgeSamplingParams:
    """Edge-based color sampling parameters."""
    enabled: bool = False
    samples: int = 36
    method: Literal['circumference', 'canny', 'exposed', 'band'] = 'circumference'


@dataclass
class OutputParams:
    """Output and extraction settings."""
    format: Literal['json', 'csv'] = 'json'
    output_path: Optional[Path] = None
    extract_dir: Optional[Path] = None
    run_name: Optional[str] = None
    no_organize: bool = False
    no_manifest: bool = False
    quantize_output: Optional[Path] = None
    save_config: Optional[Path] = None


@dataclass
class PerformanceParams:
    """Processing performance settings."""
    chunk_size: str = 'auto'


@dataclass
class CalibrationParams:
    """Radius calibration settings."""
    auto_calibrate: bool = False
    calibrate_from: Optional[str] = None


@dataclass
class JitterParams:
    """Jitter/randomization settings for breaking grid patterns.
    
    Controls random variation in circle positions and sizes to create
    more natural-looking halftone patterns.
    """
    position: int = 0  # 0-100 percentage of radius
    size: int = 0  # 0-100 percentage of radius
    seed: Optional[int] = 1  # Random seed for reproducibility
    algorithm: Literal['gaussian', 'uniform'] = 'gaussian'
    exclude: str = ''  # Colors to exclude (e.g., "ck" for cyan+black)
    drift: bool = False  # Enable drift-balanced jitter
    drift_tolerance: float = 0.2  # 0.0-1.0 balance tolerance
    drift_max_iterations: int = 10
    drift_max_step: float = 2.0
    steps: int = 1  # Number of jitter-drift iterations (each step uses seed+step offset)


@dataclass
class RenderParams:
    """Renderer configuration parameters.
    
    Controls how detected clusters are rendered to output images.
    All rendering-related options are consolidated here for easy
    configuration via CLI or config file.
    """
    method: Literal['bullseye', 'block', 'treemap', 'exact', 'flower', 'planetary', 'cmyk-blend'] = 'bullseye'
    segment_height: int = 10  # Block renderer row height
    cluster_size: int = 20  # Treemap renderer rectangle size
    scale: int = 1  # Output scale multiplier
    color_mode: Literal['full', 'cmyk'] = 'full'  # 7-color or 4-color
    diff_mode: Literal['mask', 'highlight'] = 'mask'
    output_format: Literal['svg', 'png'] = 'svg'
    # Flower/Planetary renderer specific
    petal_rotation: Literal['fixed', 'random', 'cluster-hash'] = 'fixed'
    petal_offset: float = 0.0  # Base rotation angle offset in degrees
    petal_distance: float = 0.35  # Petal center distance as fraction of black radius (flower only)
    exposed_area_sizing: bool = True  # Size petals based on visible area (flower only)
    blend_overlaps: bool = False  # Use subtractive CMY blending
    # Jitter settings (nested)
    jitter: JitterParams = field(default_factory=JitterParams)


@dataclass
class DetectionConfig:
    """Complete detection configuration.

    This is the main Parameter Object that consolidates all CLI options
    into a single, structured configuration object.

    Example usage:
        config = DetectionConfig(
            input_path=Path("image.png"),
            detection=DetectionParams(min_radius=15, max_radius=100),
            color=ColorParams(palette='cmyk-sep'),
        )
    """
    # Required
    input_path: Optional[Path] = None

    # Configuration file
    config_file: Optional[Path] = None

    # Mode preset
    mode: Optional[Literal['standard', 'halftone', 'cmyk-sep']] = None

    # Debug flag
    debug: bool = False

    # Grouped parameters
    detection: DetectionParams = field(default_factory=DetectionParams)
    methods: DetectionMethodParams = field(default_factory=DetectionMethodParams)
    color: ColorParams = field(default_factory=ColorParams)
    edge_sampling: EdgeSamplingParams = field(default_factory=EdgeSamplingParams)
    output: OutputParams = field(default_factory=OutputParams)
    performance: PerformanceParams = field(default_factory=PerformanceParams)
    calibration: CalibrationParams = field(default_factory=CalibrationParams)
    render: RenderParams = field(default_factory=RenderParams)

    def to_dict(self) -> dict:
        """Convert config to dictionary for serialization."""
        result = asdict(self)
        # Convert Path objects to strings
        for key in ['input_path', 'config_file']:
            if result[key] is not None:
                result[key] = str(result[key])
        if result['output']['output_path'] is not None:
            result['output']['output_path'] = str(result['output']['output_path'])
        if result['output']['extract_dir'] is not None:
            result['output']['extract_dir'] = str(result['output']['extract_dir'])
        if result['output']['quantize_output'] is not None:
            result['output']['quantize_output'] = str(result['output']['quantize_output'])
        if result['output']['save_config'] is not None:
            result['output']['save_config'] = str(result['output']['save_config'])
        return result

    @classmethod
    def from_cli_args(
        cls,
        input: Optional[Path],
        config: Optional[Path],
        mode: Optional[str],
        debug: bool,
        min_radius: int,
        max_radius: int,
        min_distance: int,
        sensitivity: str,
        min_confidence: Optional[int],
        convex_edge: bool,
        color_separation: bool,
        use_histogram: bool,
        sensitive_occlusion: bool,
        morph_enhance: bool,
        palette: str,
        num_colors: int,
        color_tolerance: int,
        max_colors: Optional[int],
        exclude_background: bool,
        edge_sampling: bool,
        edge_samples: int,
        edge_method: str,
        format: str,
        output: Optional[Path],
        extract: Optional[Path],
        run_name: Optional[str],
        no_organize: bool,
        no_manifest: bool,
        quantize_output: Optional[Path],
        save_config: Optional[Path],
        chunk_size: str,
        auto_calibrate: bool,
        calibrate_from: Optional[str],
        # Render parameters
        render_method: str = 'bullseye',
        segment_height: int = 10,
        cluster_size: int = 20,
        render_scale: int = 1,
        color_mode: str = 'full',
        diff_mode: str = 'mask',
        output_format: str = 'svg',
        petal_rotation: str = 'fixed',
        petal_offset: float = 0.0,
        petal_distance: float = 0.35,
        exposed_area_sizing: bool = True,
        blend_overlaps: bool = False,
        jitter_position: int = 0,
        jitter_size: int = 0,
        jitter_seed: Optional[int] = 1,
        jitter_algorithm: str = 'gaussian',
        jitter_exclude: str = '',
        drift: bool = False,
        drift_tolerance: float = 0.2,
        drift_max_iterations: int = 10,
        drift_max_step: float = 2.0,
    ) -> 'DetectionConfig':
        """Create DetectionConfig from CLI arguments.

        This factory method maps flat CLI arguments to the nested dataclass structure.
        """
        return cls(
            input_path=input,
            config_file=config,
            mode=mode,
            debug=debug,
            detection=DetectionParams(
                min_radius=min_radius,
                max_radius=max_radius,
                min_distance=min_distance,
                sensitivity=sensitivity,
                min_confidence=min_confidence,
            ),
            methods=DetectionMethodParams(
                convex_edge=convex_edge,
                color_separation=color_separation,
                use_histogram=use_histogram,
                sensitive_occlusion=sensitive_occlusion,
                morph_enhance=morph_enhance,
            ),
            color=ColorParams(
                palette=palette,
                num_colors=num_colors,
                color_tolerance=color_tolerance,
                max_colors=max_colors,
                exclude_background=exclude_background,
            ),
            edge_sampling=EdgeSamplingParams(
                enabled=edge_sampling,
                samples=edge_samples,
                method=edge_method,
            ),
            output=OutputParams(
                format=format,
                output_path=output,
                extract_dir=extract,
                run_name=run_name,
                no_organize=no_organize,
                no_manifest=no_manifest,
                quantize_output=quantize_output,
                save_config=save_config,
            ),
            performance=PerformanceParams(
                chunk_size=chunk_size,
            ),
            calibration=CalibrationParams(
                auto_calibrate=auto_calibrate,
                calibrate_from=calibrate_from,
            ),
            render=RenderParams(
                method=render_method,
                segment_height=segment_height,
                cluster_size=cluster_size,
                scale=render_scale,
                color_mode=color_mode,
                diff_mode=diff_mode,
                output_format=output_format,
                petal_rotation=petal_rotation,
                petal_offset=petal_offset,
                petal_distance=petal_distance,
                exposed_area_sizing=exposed_area_sizing,
                blend_overlaps=blend_overlaps,
                jitter=JitterParams(
                    position=jitter_position,
                    size=jitter_size,
                    seed=jitter_seed,
                    algorithm=jitter_algorithm,
                    exclude=jitter_exclude,
                    drift=drift,
                    drift_tolerance=drift_tolerance,
                    drift_max_iterations=drift_max_iterations,
                    drift_max_step=drift_max_step,
                ),
            ),
        )
