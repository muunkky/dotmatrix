"""Command-line interface for DotMatrix."""

import click
from click_option_group import optgroup, MutuallyExclusiveOptionGroup
from pathlib import Path
import sys
import cv2

from . import __version__
from .config_loader import load_config, merge_config_with_cli_args, validate_config


# Create the main CLI group
@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version=__version__, prog_name='dotmatrix')
# Core Options (always shown first)
@click.option(
    '--config', '-c',
    type=click.Path(exists=True, path_type=Path),
    help='Load parameters from config file (JSON or YAML)'
)
@click.option(
    '--input', '-i',
    type=click.Path(exists=True, path_type=Path),
    help='Input image file path (PNG, JPG, JPEG)'
)
@click.option(
    '--output', '-o',
    type=click.Path(path_type=Path),
    help='Output file path (default: stdout)'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['json', 'csv'], case_sensitive=False),
    default='json',
    help='Output format (default: json)'
)
@click.option(
    '--debug',
    is_flag=True,
    help='Enable debug output'
)
@click.option(
    '--mode', '-m',
    type=click.Choice(['standard', 'halftone', 'cmyk-sep'], case_sensitive=False),
    default=None,
    help='Detection preset: standard (simple circles), halftone (overlapping CMYK), cmyk-sep (ink separation)'
)
# Detection Options
@optgroup.group('Detection Options', help='Circle detection parameters')
@optgroup.option(
    '--min-radius',
    type=int,
    default=10,
    help='Minimum circle radius in pixels (default: 10)'
)
@optgroup.option(
    '--max-radius',
    type=int,
    default=500,
    help='Maximum circle radius in pixels (default: 500)'
)
@optgroup.option(
    '--min-distance',
    type=int,
    default=20,
    help='Minimum distance between circle centers (default: 20)'
)
@optgroup.option(
    '--sensitivity',
    type=click.Choice(['strict', 'normal', 'relaxed'], case_sensitive=False),
    default='normal',
    help='Detection sensitivity preset (default: normal)'
)
@optgroup.option(
    '--min-confidence',
    type=click.IntRange(0, 100),
    help='Minimum confidence score (0-100)'
)
# Detection Methods
@optgroup.group('Detection Methods', help='Algorithm selection for different image types')
@optgroup.option(
    '--convex-edge',
    is_flag=True,
    help='Convex edge detection for overlapping circles (best for CMYK/halftone)'
)
@optgroup.option(
    '--color-separation',
    is_flag=True,
    help='Separate by color first, then detect per color (good for overlapping)'
)
@optgroup.option(
    '--use-histogram',
    is_flag=True,
    help='Histogram-based color palette extraction (recommended for CMYK)'
)
@optgroup.option(
    '--sensitive-occlusion',
    is_flag=True,
    help='Lower thresholds for heavily occluded circles'
)
@optgroup.option(
    '--morph-enhance',
    is_flag=True,
    help='Morphological enhancement for fragmented regions'
)
# Color Options
@optgroup.group('Color Options', help='Color detection and grouping')
@optgroup.option(
    '--palette',
    type=str,
    default='cmyk',
    help='Color palette: auto, cmyk, cmyk-sep, rgb, or custom "R,G,B;R,G,B"'
)
@optgroup.option(
    '--num-colors',
    type=int,
    default=6,
    help='Colors to detect with --palette auto (default: 6)'
)
@optgroup.option(
    '--color-tolerance',
    type=int,
    default=20,
    help='RGB distance for color grouping (default: 20)'
)
@optgroup.option(
    '--max-colors',
    type=int,
    help='Maximum color groups with k-means (only with --extract)'
)
@optgroup.option(
    '--exclude-background',
    is_flag=True,
    help='Exclude near-white background (RGB > 240)'
)
# Edge Sampling Options
@optgroup.group('Edge Sampling', help='Edge-based color sampling for overlapping circles')
@optgroup.option(
    '--edge-sampling',
    is_flag=True,
    help='Enable edge-based color sampling'
)
@optgroup.option(
    '--edge-samples',
    type=int,
    default=36,
    help='Sample points around edge (default: 36)'
)
@optgroup.option(
    '--edge-method',
    type=click.Choice(['circumference', 'canny', 'exposed', 'band'], case_sensitive=False),
    default='circumference',
    help='Sampling method (default: circumference)'
)
# Output/Extract Options
@optgroup.group('Output Options', help='Extraction and output settings')
@optgroup.option(
    '--extract', '-e',
    type=click.Path(path_type=Path),
    default=None,
    help='Extract circles to PNGs by color'
)
@optgroup.option(
    '--run-name',
    type=str,
    help='Custom name for this run'
)
@optgroup.option(
    '--no-organize',
    is_flag=True,
    help='Disable subdirectory creation for --extract'
)
@optgroup.option(
    '--no-manifest',
    is_flag=True,
    help='Disable manifest.json generation'
)
@optgroup.option(
    '--quantize-output',
    type=click.Path(path_type=Path),
    help='Save quantized image (debug)'
)
@optgroup.option(
    '--save-config',
    type=click.Path(path_type=Path),
    help='Save settings to config file'
)
# Performance Options
@optgroup.group('Performance', help='Processing performance settings')
@optgroup.option(
    '--chunk-size',
    type=str,
    default='auto',
    help='Tile size: "auto", pixel size, or "0" to disable'
)
# Calibration Options
@optgroup.group('Calibration', help='Radius calibration from reference')
@optgroup.option(
    '--auto-calibrate',
    is_flag=True,
    help='Auto-calibrate radius from darkest color'
)
@optgroup.option(
    '--calibrate-from',
    type=str,
    help='Calibrate from specific color (e.g., "black")'
)
def cli(ctx, config, input, output, format, debug, extract, mode, min_radius, max_radius, min_distance, color_tolerance, max_colors, sensitivity, min_confidence, edge_sampling, edge_samples, edge_method, exclude_background, use_histogram, color_separation, convex_edge, palette, num_colors, quantize_output, run_name, no_organize, save_config, no_manifest, chunk_size, sensitive_occlusion, morph_enhance, auto_calibrate, calibrate_from):
    """DotMatrix: Detect circles in images.

    Identifies the center coordinates, radius, and color of circles in images,
    even when circles overlap.

    \b
    QUICK START:
      dotmatrix -i image.png                    # Basic detection, JSON output
      dotmatrix -i image.png -e output/         # Extract circles to PNGs by color
      dotmatrix -i image.png -m halftone        # Halftone/overlapping circles

    \b
    COMMON USE CASES:
      Simple circles:     -m standard
      CMYK halftone:      -m halftone (or --convex-edge --palette cmyk)
      Ink separation:     -m cmyk-sep (extracts each ink color plate)

    \b
    PRESETS (--mode):
      standard   - Simple non-overlapping circles (fastest)
      halftone   - Overlapping CMYK halftone dots
      cmyk-sep   - CMYK ink separation with subtractive color logic

    Use 'dotmatrix runs list' to view past detection runs.
    """
    # If no subcommand invoked, run detect (for backward compatibility)
    if ctx.invoked_subcommand is None:
        _do_detect(config, input, output, format, debug, extract, mode, min_radius, max_radius,
                   min_distance, color_tolerance, max_colors, sensitivity, min_confidence,
                   edge_sampling, edge_samples, edge_method, exclude_background, use_histogram,
                   color_separation, convex_edge, palette, num_colors, quantize_output, run_name,
                   no_organize, save_config, no_manifest, chunk_size, sensitive_occlusion, morph_enhance,
                   auto_calibrate, calibrate_from)


# ============================================================================
# Helper functions for _do_detect (extracted for readability)
# ============================================================================

def _apply_mode_presets(mode, convex_edge, palette, sensitive_occlusion, morph_enhance, debug):
    """Apply mode preset settings, returning updated values."""
    if not mode:
        return convex_edge, palette, sensitive_occlusion, morph_enhance

    mode_lower = mode.lower()
    if mode_lower == 'standard':
        # Standard mode: simple Hough circle detection (default behavior)
        if convex_edge is None or not convex_edge:
            convex_edge = False
    elif mode_lower == 'halftone':
        # Halftone mode: convex edge detection with CMYK palette
        convex_edge = True
        if palette == 'cmyk':  # Only override if not explicitly set
            palette = 'cmyk'
        sensitive_occlusion = True
        morph_enhance = True
    elif mode_lower == 'cmyk-sep':
        # CMYK separation mode: ink separation with AND logic
        convex_edge = True
        palette = 'cmyk-sep'
        sensitive_occlusion = True
        morph_enhance = True

    if debug:
        click.echo(f"Mode '{mode}' preset applied", err=True)

    return convex_edge, palette, sensitive_occlusion, morph_enhance


def _validate_inputs(input_path, extract, max_colors):
    """Validate input parameters, exit with error if invalid."""
    # Validate required --input parameter
    if not input_path:
        click.echo("Error: --input is required (either via CLI or config file)", err=True)
        sys.exit(1)

    # Validate --max-colors requires --extract
    if max_colors is not None and not extract:
        click.echo(
            "Error: --max-colors can only be used with --extract",
            err=True
        )
        sys.exit(1)

    # Validate file extension
    valid_extensions = {'.png', '.jpg', '.jpeg'}
    if input_path.suffix.lower() not in valid_extensions:
        click.echo(
            f"Error: Invalid file format '{input_path.suffix}'. "
            f"Supported formats: {', '.join(valid_extensions)}",
            err=True
        )
        sys.exit(1)


def _handle_extraction(results, image_shape, extract, run_name, no_organize,
                       color_tolerance, max_colors, no_manifest, input_path,
                       min_radius, max_radius, min_distance, sensitivity,
                       min_confidence, convex_edge, palette, edge_sampling,
                       edge_samples, edge_method, format, debug):
    """Handle extracting circles to images and generating manifest."""
    from .run_manager import create_run_directory, copy_input_file
    from .image_extractor import extract_circles_to_images, generate_cmyk_layer_files

    # Create organized output directory (unless --no-organize)
    output_dir = create_run_directory(
        base_dir=extract,
        run_name=run_name,
        organize=not no_organize
    )

    if debug:
        click.echo(f"Extracting circles to: {output_dir}", err=True)
        if max_colors:
            click.echo(f"Using k-means clustering with max_colors={max_colors}", err=True)

    # Copy input file to run directory for reproducibility
    if input_path:
        copied_input = copy_input_file(input_path, output_dir)
        if debug:
            click.echo(f"Copied input file to: {copied_input}", err=True)

    # Check if using CMYK mode (cmyk or cmyk-sep palette with convex_edge)
    use_cmyk_layers = convex_edge and palette in ('cmyk', 'cmyk-sep')

    if use_cmyk_layers:
        # Generate named CMYK layer files (cyan.png, magenta.png, yellow.png, black.png)
        layer_files = generate_cmyk_layer_files(
            results,
            image_shape=image_shape,
            output_dir=output_dir,
            tolerance=color_tolerance
        )
        extracted_files = list(layer_files.values())

        click.echo(f"Generated {len(layer_files)} CMYK layer file(s) to {output_dir}/")
        for layer_name, filepath in layer_files.items():
            click.echo(f"  - {layer_name}.png")
    else:
        # Use color-grouped extraction for non-CMYK modes
        extracted_files = extract_circles_to_images(
            results,
            image_shape=image_shape,
            output_dir=output_dir,
            prefix="circles",
            tolerance=color_tolerance,
            max_colors=max_colors
        )

        click.echo(f"Extracted {len(extracted_files)} color group(s) to {output_dir}/")
        for filepath in extracted_files:
            click.echo(f"  - {filepath.name}")

    # Generate manifest unless disabled
    if not no_manifest:
        from .manifest import generate_manifest, write_manifest

        # Build color names mapping for convex-edge mode
        color_names = None
        if convex_edge:
            from .convex_detector import get_color_name
            color_names = {
                color: get_color_name(color)
                for _, color in results
            }

        # Collect settings for manifest
        manifest_settings = {
            'min_radius': min_radius,
            'max_radius': max_radius,
            'min_distance': min_distance,
            'sensitivity': sensitivity,
            'min_confidence': min_confidence,
            'convex_edge': convex_edge,
            'palette': palette if convex_edge else None,
            'color_tolerance': color_tolerance,
            'max_colors': max_colors,
            'edge_sampling': edge_sampling,
            'edge_samples': edge_samples,
            'edge_method': edge_method,
            'format': format,
        }

        manifest = generate_manifest(
            source_file=input_path,
            settings=manifest_settings,
            results=results,
            output_files=extracted_files,
            color_names=color_names,
        )

        manifest_path = write_manifest(output_dir, manifest)

        if debug:
            click.echo(f"Manifest written to: {manifest_path}", err=True)

    if debug:
        click.echo("Extraction complete!", err=True)


def _format_and_output_results(results, format, output, extract, debug):
    """Format results and write to output or stdout."""
    from .formatter import format_json, format_csv

    # Format output (skip if only extracting)
    if not extract or output or not extract:
        if format.lower() == 'json':
            formatted_output = format_json(results)
        else:  # csv
            formatted_output = format_csv(results)

        # Write to output or stdout
        if output:
            output.write_text(formatted_output)
            if debug:
                click.echo(f"Results written to: {output}", err=True)
        elif not extract:  # Only print to stdout if not extracting
            click.echo(formatted_output)


def _do_detect(config, input, output, format, debug, extract, mode, min_radius, max_radius, min_distance, color_tolerance, max_colors, sensitivity, min_confidence, edge_sampling, edge_samples, edge_method, exclude_background, use_histogram, color_separation, convex_edge, palette, num_colors, quantize_output, run_name, no_organize, save_config, no_manifest, chunk_size='auto', sensitive_occlusion=False, morph_enhance=False, auto_calibrate=False, calibrate_from=None):
    """Internal function for circle detection."""
    # Apply mode presets - these set defaults that can be overridden by explicit flags
    convex_edge, palette, sensitive_occlusion, morph_enhance = _apply_mode_presets(
        mode, convex_edge, palette, sensitive_occlusion, morph_enhance, debug
    )

    # Load configuration file if provided
    if config:
        try:
            file_config = load_config(config)
            validate_config(file_config)

            # Build CLI args dict (only explicitly provided values)
            # Use Click's parameter source to distinguish CLI args from defaults
            ctx = click.get_current_context()
            cli_args = {}

            # Check all parameters - only add if explicitly provided by user
            for param_name in ['input', 'output', 'format', 'debug', 'extract',
                              'min_radius', 'max_radius', 'min_distance',
                              'color_tolerance', 'max_colors', 'sensitivity',
                              'min_confidence', 'edge_sampling', 'edge_samples',
                              'edge_method', 'exclude_background', 'use_histogram', 'color_separation',
                              'convex_edge', 'palette', 'num_colors', 'quantize_output', 'run_name', 'no_organize',
                              'save_config', 'no_manifest', 'chunk_size']:
                if param_name in ctx.params:
                    source = ctx.get_parameter_source(param_name)
                    # Only add if NOT from default (i.e., from CLI or environment)
                    if source.name != 'DEFAULT':
                        cli_args[param_name] = locals()[param_name]

            # Merge config with CLI args (CLI takes precedence)
            merged = merge_config_with_cli_args(file_config, cli_args)

            # Apply merged config
            input = merged.get('input', input)
            output = merged.get('output', output)
            format = merged.get('format', format)
            debug = merged.get('debug', debug)
            extract = merged.get('extract', extract)
            min_radius = merged.get('min_radius', min_radius)
            max_radius = merged.get('max_radius', max_radius)
            min_distance = merged.get('min_distance', min_distance)
            color_tolerance = merged.get('color_tolerance', color_tolerance)
            max_colors = merged.get('max_colors', max_colors)
            sensitivity = merged.get('sensitivity', sensitivity)
            min_confidence = merged.get('min_confidence', min_confidence)
            edge_sampling = merged.get('edge_sampling', edge_sampling)
            edge_samples = merged.get('edge_samples', edge_samples)
            edge_method = merged.get('edge_method', edge_method)
            exclude_background = merged.get('exclude_background', exclude_background)
            use_histogram = merged.get('use_histogram', use_histogram)
            color_separation = merged.get('color_separation', color_separation)
            convex_edge = merged.get('convex_edge', convex_edge)
            palette = merged.get('palette', palette)
            num_colors = merged.get('num_colors', num_colors)
            quantize_output = merged.get('quantize_output', quantize_output)
            run_name = merged.get('run_name', run_name)
            no_organize = merged.get('no_organize', no_organize)
            save_config = merged.get('save_config', save_config)
            no_manifest = merged.get('no_manifest', no_manifest)
            chunk_size = merged.get('chunk_size', chunk_size)

            if debug:
                click.echo(f"Loaded configuration from: {config}", err=True)
                click.echo(f"  Merged min_radius: {min_radius}", err=True)
                click.echo(f"  Merged min_distance: {min_distance}", err=True)
                click.echo(f"  Merged sensitivity: {sensitivity}", err=True)
                click.echo(f"  Merged edge_sampling: {edge_sampling}", err=True)
                click.echo(f"  Merged edge_method: {edge_method}", err=True)

        except Exception as e:
            click.echo(f"Error loading config: {e}", err=True)
            sys.exit(1)

    # Validate inputs (exits on failure)
    _validate_inputs(input, extract, max_colors)

    if debug:
        click.echo(f"Debug mode enabled", err=True)
        click.echo(f"Input: {input}", err=True)
        click.echo(f"Output: {output or 'stdout'}", err=True)
        click.echo(f"Format: {format}", err=True)

    # Save config if requested
    if save_config:
        from .config_loader import save_config as do_save_config

        # Collect all current settings
        current_settings = {
            'min_radius': min_radius,
            'max_radius': max_radius,
            'min_distance': min_distance,
            'sensitivity': sensitivity,
            'min_confidence': min_confidence,
            'convex_edge': convex_edge,
            'palette': palette,
            'color_tolerance': color_tolerance,
            'max_colors': max_colors,
            'edge_sampling': edge_sampling,
            'edge_samples': edge_samples,
            'edge_method': edge_method,
            'exclude_background': exclude_background,
            'use_histogram': use_histogram,
            'format': format,
            'run_name': run_name,
            'no_organize': no_organize,
        }

        try:
            do_save_config(save_config, current_settings)
            click.echo(f"Configuration saved to: {save_config}", err=True)
        except ValueError as e:
            click.echo(f"Error saving config: {e}", err=True)
            sys.exit(1)

        # If only saving config (no input), exit early
        if not input:
            sys.exit(0)

    try:
        # Import modules
        from .image_loader import load_image, get_image_megapixels
        from .circle_detector import detect_circles
        from .color_extractor import extract_color
        from .formatter import format_json, format_csv
        from .image_extractor import extract_circles_to_images

        if debug:
            click.echo(f"DotMatrix v{__version__}", err=True)
            click.echo(f"Loading image: {input}", err=True)

        # 1. Load image
        image = load_image(input)

        if debug:
            click.echo(f"Image loaded: {image.shape}", err=True)
            click.echo("Detecting circles...", err=True)

        # Check image size and warn for large images with convex detection
        megapixels = get_image_megapixels(image)
        LARGE_IMAGE_THRESHOLD_MP = 20  # Per ADR-001

        if convex_edge and megapixels > LARGE_IMAGE_THRESHOLD_MP:
            click.echo(
                f"Warning: Large image detected ({megapixels:.1f} megapixels). "
                f"Convex edge detection may take 30+ seconds. "
                f"Consider using standard detection for faster results.",
                err=True
            )

        # 2. Detect circles - use convex-edge mode if requested
        if convex_edge:
            # Convex edge detection for overlapping circles
            from .convex_detector import (
                detect_all_circles, parse_palette, get_color_name,
                process_chunked, calculate_chunk_size, PALETTES,
                detect_with_calibration, detect_circles_cmyk_separation,
                CMYK_INK_COLORS
            )

            # Show progress message for convex detection (can be slow for large images)
            if megapixels > 5:  # Show progress for images > 5 MP
                click.echo(f"Detecting circles (convex edge analysis)...", err=True)

            if debug:
                click.echo(f"Using convex edge detection with palette: {palette}", err=True)

            # Convert BGR to RGB for convex detector (needed for both auto and preset)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Track if we're in CMYK separation mode (uses different processing path)
            cmyk_sep_mode = palette.lower() == 'cmyk-sep'

            # Handle CMYK separation mode (special palette for overlapping CMYK halftones)
            if cmyk_sep_mode:
                click.echo("Using CMYK ink separation mode (AND logic for overlapping colors)", err=True)

                # Debug callback for CMYK separation
                def cmyk_debug_cb(ink_name, mask, circles):
                    if debug:
                        click.echo(f"  {ink_name}: {len(circles)} circle(s) detected", err=True)

                detected_circles = detect_circles_cmyk_separation(
                    image_rgb,
                    min_radius=min_radius,
                    max_radius=max_radius,
                    ink_threshold=100,  # Could make this configurable
                    debug_callback=cmyk_debug_cb if debug else None,
                    sensitive_mode=sensitive_occlusion,
                    morphological_enhance=morph_enhance
                )
                quantized = None  # No quantized image in separation mode
                color_palette = list(CMYK_INK_COLORS.values())  # For compatibility

                if debug:
                    click.echo(f"Total detected: {len(detected_circles)} circle(s)", err=True)

            # Handle auto-palette detection
            elif palette.lower() == 'auto':
                from .color_palette_detector import (
                    detect_palette_for_convex, format_detected_palette
                )

                if debug:
                    click.echo(f"Auto-detecting color palette ({num_colors} colors)...", err=True)

                color_palette = detect_palette_for_convex(
                    image_rgb, n_colors=num_colors
                )

                # Show detected palette to user
                palette_desc = format_detected_palette(color_palette)
                click.echo(f"Detected palette: {palette_desc}", err=True)
            else:
                # Use preset or custom palette
                try:
                    color_palette = parse_palette(palette)
                except ValueError as e:
                    click.echo(f"Error: {e}", err=True)
                    sys.exit(1)

            # Skip palette-based processing if already processed in cmyk-sep mode
            if not cmyk_sep_mode:
                if debug:
                    click.echo(f"Palette colors: {len(color_palette)}", err=True)
                    for i, color in enumerate(color_palette):
                        click.echo(f"  {i+1}. {get_color_name(color)} RGB{color}", err=True)

            # Run palette-based detection (skip if already processed in cmyk-sep mode)
            if not cmyk_sep_mode:
                # Determine chunk size for processing
                use_chunked = False
                actual_chunk_size = 0
                if chunk_size != '0':
                    if chunk_size == 'auto':
                        # Auto: use chunking for images > 20 MP
                        if megapixels > LARGE_IMAGE_THRESHOLD_MP:
                            actual_chunk_size = calculate_chunk_size(image_rgb.shape, max_radius)
                            use_chunked = True
                    else:
                        # Explicit size
                        try:
                            actual_chunk_size = int(chunk_size)
                            use_chunked = True
                        except ValueError:
                            click.echo(f"Error: Invalid chunk-size '{chunk_size}'. Use 'auto', '0', or a pixel size.", err=True)
                            sys.exit(1)

                if use_chunked:
                    # Use chunked processing for large images
                    if debug:
                        click.echo(f"Using chunked processing with chunk size: {actual_chunk_size}px", err=True)

                    # Progress callback to show tile progress
                    def progress_cb(tile_num, total_tiles):
                        click.echo(f"Processing tile {tile_num}/{total_tiles}...", err=True)

                    detected_circles = process_chunked(
                        image_rgb,
                        palette=color_palette,
                        chunk_size=actual_chunk_size,
                        max_radius=max_radius,
                        min_radius=min_radius,
                        exclude_background=True,
                        progress_callback=progress_cb if not debug else None,
                        debug_callback=None,
                        sensitive_mode=sensitive_occlusion,
                        morphological_enhance=morph_enhance
                    )
                    quantized = None  # Not available in chunked mode
                else:
                    # Debug callback to show per-color progress
                    def debug_cb(color, mask, circles):
                        if debug:
                            click.echo(f"  {get_color_name(color)}: {len(circles)} circle(s) detected", err=True)

                    # Use calibration mode if requested
                    if auto_calibrate or calibrate_from:
                        if debug:
                            if calibrate_from:
                                click.echo(f"Calibrating radius from color: {calibrate_from}", err=True)
                            else:
                                click.echo("Auto-calibrating radius from reference color...", err=True)

                        # Detect with calibration
                        detected_circles, quantized, calibration = detect_with_calibration(
                            image_rgb,
                            color_palette,
                            initial_min_radius=min_radius,
                            initial_max_radius=max_radius,
                            calibrate_from=calibrate_from,
                            auto_calibrate=auto_calibrate,
                            exclude_background=True,
                            debug_callback=debug_cb if debug else None,
                            sensitive_mode=sensitive_occlusion,
                            morphological_enhance=morph_enhance
                        )

                        # Report calibration results
                        if calibration:
                            click.echo(
                                f"Calibration: {get_color_name(calibration.reference_color)} reference "
                                f"({calibration.reference_count} circles), "
                                f"radius {calibration.min_radius}-{calibration.max_radius}px "
                                f"(mean={calibration.mean_radius:.1f}, std={calibration.std_radius:.1f})",
                                err=True
                            )
                        else:
                            click.echo("Warning: Calibration failed (insufficient reference circles), using original radius bounds", err=True)
                    else:
                        # Standard detection without calibration
                        detected_circles, quantized = detect_all_circles(
                            image_rgb,
                            color_palette,
                            min_radius=min_radius,
                            max_radius=max_radius,
                            exclude_background=True,
                            debug_callback=debug_cb if debug else None,
                            sensitive_mode=sensitive_occlusion,
                            morphological_enhance=morph_enhance
                        )

            if debug:
                click.echo(f"Total detected: {len(detected_circles)} circle(s)", err=True)

            # Save quantized image if requested
            if quantize_output:
                if quantized is not None:
                    quantized_bgr = cv2.cvtColor(quantized, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(str(quantize_output), quantized_bgr)
                    if debug:
                        click.echo(f"Quantized image saved to: {quantize_output}", err=True)
                else:
                    click.echo("Warning: Quantized image not available in chunked mode", err=True)

            if len(detected_circles) == 0:
                click.echo("No circles detected in image.", err=True)
                sys.exit(0)

            # Convert to results format (circle, color) tuples
            # Create a simple Circle-like object for compatibility with formatter
            from dataclasses import dataclass
            @dataclass
            class SimpleCircle:
                center_x: int
                center_y: int
                radius: int
                confidence: float = 100.0

            results = []
            for dc in detected_circles:
                circle = SimpleCircle(dc.x, dc.y, dc.radius, dc.confidence)
                results.append((circle, dc.color))

        else:
            # Standard detection path
            circles = detect_circles(
                image,
                min_radius=min_radius,
                max_radius=max_radius,
                min_distance=min_distance,
                sensitivity=sensitivity
            )

            if debug:
                click.echo(f"Detected {len(circles)} circle(s)", err=True)

            # Filter by confidence if specified
            if min_confidence is not None:
                circles = [c for c in circles if c.confidence >= min_confidence]
                if debug:
                    click.echo(f"After confidence filter (>={min_confidence}): {len(circles)} circle(s)", err=True)

            if len(circles) == 0:
                click.echo("No circles detected in image.", err=True)
                sys.exit(0)

            # 3. Extract colors for each circle
            # If using histogram mode, extract color palette first
            color_palette = None
            if use_histogram and max_colors:
                from .histogram_colors import extract_color_palette
                if debug:
                    click.echo(f"Extracting color palette (top {max_colors} colors excluding white)...", err=True)
                # Convert BGR to RGB for histogram analysis
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                color_palette = extract_color_palette(
                    image_rgb,
                    n_colors=max_colors,
                    exclude_background=exclude_background,
                    mode='histogram'
                )
                if debug:
                    click.echo(f"Color palette extracted: {len(color_palette)} colors", err=True)
                    for i, color in enumerate(color_palette, 1):
                        click.echo(f"  {i}. RGB{color}", err=True)

            results = []
            for circle in circles:
                if debug:
                    sampling_method = "edge" if edge_sampling else "area"
                    if edge_sampling:
                        sampling_method = f"edge ({edge_method})"
                    click.echo(f"  Extracting color for {circle} (method: {sampling_method})", err=True)

                # Sample color from circle
                if color_palette:
                    # Use new function that counts palette color matches
                    from .color_extractor import extract_color_with_palette
                    color = extract_color_with_palette(
                        image,
                        circle,
                        palette=color_palette,
                        num_samples=edge_samples,
                        max_distance=50.0
                    )
                    if debug:
                        click.echo(f"    Assigned to palette RGB{color}", err=True)
                else:
                    # Old method for non-histogram mode
                    sampled_color = extract_color(
                        image,
                        circle,
                        use_edge_sampling=edge_sampling,
                        num_samples=edge_samples,
                        edge_method=edge_method,
                        all_circles=circles if edge_method == 'exposed' else None
                    )
                    color = sampled_color

                # Filter out background colors if requested (only in non-histogram mode)
                if not color_palette and exclude_background:
                    r, g, b = color
                    # Exclude near-white colors (RGB > 240)
                    if r > 240 and g > 240 and b > 240:
                        if debug:
                            click.echo(f"    Skipping background color: RGB({r},{g},{b})", err=True)
                        continue

                results.append((circle, color))

        # 4. Extract to separate PNG images if requested
        if extract:
            _handle_extraction(
                results, image.shape[:2], extract, run_name, no_organize,
                color_tolerance, max_colors, no_manifest, input,
                min_radius, max_radius, min_distance, sensitivity,
                min_confidence, convex_edge, palette, edge_sampling,
                edge_samples, edge_method, format, debug
            )

        # 5. Format and output results
        _format_and_output_results(results, format, output, extract, debug)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# ============================================================================
# Runs subcommand group for managing past runs
# ============================================================================

@cli.group()
def runs():
    """Manage and query past detection runs.

    Use these commands to list, view, and replay previous detection runs
    based on their saved manifest files.
    """
    pass


@runs.command('list')
@click.option(
    '--dir', '-d',
    type=click.Path(exists=True, path_type=Path),
    default='./output',
    help='Output directory to search (default: ./output)'
)
@click.option(
    '--source', '-s',
    help='Filter by source filename (substring match)'
)
@click.option(
    '--after',
    help='Filter runs after date (YYYY-MM-DD format)'
)
def runs_list(dir, source, after):
    """List all detection runs in the output directory.

    Scans for directories containing manifest.json files and displays
    a summary table with run name, date, source file, and circle count.

    Examples:
        dotmatrix runs list
        dotmatrix runs list --source image.png
        dotmatrix runs list --after 2025-11-20
    """
    from .runs import list_runs, format_runs_table

    runs_data = list_runs(dir, source_filter=source, after_date=after)
    click.echo(format_runs_table(runs_data))


@runs.command('show')
@click.argument('run_name')
@click.option(
    '--dir', '-d',
    type=click.Path(exists=True, path_type=Path),
    default='./output',
    help='Output directory (default: ./output)'
)
def runs_show(run_name, dir):
    """Display full manifest details for a specific run.

    Shows all metadata including settings, source file info,
    and detection results for the specified run.

    Example:
        dotmatrix runs show run_20251125_143022
    """
    from .runs import find_run_by_name, get_run_info
    from .manifest import get_manifest_summary
    import json

    run_dir = find_run_by_name(dir, run_name)
    if run_dir is None:
        click.echo(f"Run '{run_name}' not found in {dir}", err=True)
        sys.exit(1)

    info = get_run_info(run_dir)
    if info is None:
        click.echo(f"Could not read manifest for '{run_name}'", err=True)
        sys.exit(1)

    manifest = info['manifest']

    # Pretty print the manifest
    click.echo(f"Run: {info['name']}")
    click.echo(f"Date: {info['date']}")
    click.echo(f"Source: {info['source']}")
    click.echo()
    click.echo("Settings:")
    for key, value in manifest.get('settings', {}).items():
        click.echo(f"  {key}: {value}")
    click.echo()
    click.echo("Results:")
    results = manifest.get('results', {})
    click.echo(f"  Total circles: {results.get('total_circles', 0)}")
    by_color = results.get('circles_by_color', {})
    if by_color:
        click.echo(f"  By color: {', '.join(f'{k}={v}' for k, v in by_color.items())}")
    click.echo()
    click.echo("Output files:")
    for f in manifest.get('output_files', []):
        click.echo(f"  {f}")


@runs.command('replay')
@click.argument('run_name')
@click.option(
    '--dir', '-d',
    type=click.Path(exists=True, path_type=Path),
    default='./output',
    help='Output directory (default: ./output)'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Print the command instead of executing it'
)
def runs_replay(run_name, dir, dry_run):
    """Re-run detection with the same settings as a previous run.

    Constructs and executes (or prints) the dotmatrix command needed
    to reproduce a previous detection run with identical settings.

    Examples:
        dotmatrix runs replay run_20251125_143022
        dotmatrix runs replay run_20251125_143022 --dry-run
    """
    from .runs import find_run_by_name, get_run_info, get_replay_settings
    import subprocess

    run_dir = find_run_by_name(dir, run_name)
    if run_dir is None:
        click.echo(f"Run '{run_name}' not found in {dir}", err=True)
        sys.exit(1)

    info = get_run_info(run_dir)
    if info is None:
        click.echo(f"Could not read manifest for '{run_name}'", err=True)
        sys.exit(1)

    settings = get_replay_settings(info['manifest'])

    # Build command args
    cmd = ['python3', '-m', 'dotmatrix']

    source = settings.pop('source', None)
    if source:
        cmd.extend(['-i', source])

    # Map settings to CLI flags
    flag_map = {
        'min_radius': '--min-radius',
        'max_radius': '--max-radius',
        'min_distance': '--min-distance',
        'color_tolerance': '--color-tolerance',
        'max_colors': '--max-colors',
        'sensitivity': '--sensitivity',
        'min_confidence': '--min-confidence',
        'edge_sampling': '--edge-sampling',
        'edge_samples': '--edge-samples',
        'edge_method': '--edge-method',
        'palette': '--palette',
        'format': '--format',
    }

    bool_flags = {
        'convex_edge': '--convex-edge',
        'exclude_background': '--exclude-background',
        'use_histogram': '--use-histogram',
        'color_separation': '--color-separation',
        'quantize_output': '--quantize-output',
    }

    for key, value in settings.items():
        # Skip boolean values in flag_map (they should use bool_flags)
        if key in flag_map and value is not None and not isinstance(value, bool):
            cmd.extend([flag_map[key], str(value)])
        elif key in bool_flags and value is True:
            cmd.append(bool_flags[key])

    cmd_str = ' '.join(cmd)

    if dry_run:
        click.echo(cmd_str)
    else:
        click.echo(f"Running: {cmd_str}")
        result = subprocess.run(cmd, capture_output=False)
        sys.exit(result.returncode)


# For backward compatibility, expose cli as main
main = cli


if __name__ == '__main__':
    cli()
