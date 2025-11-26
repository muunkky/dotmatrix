"""Command-line interface for DotMatrix."""

import click
from pathlib import Path
import sys
import cv2

from . import __version__
from .config_loader import load_config, merge_config_with_cli_args, validate_config


# Create the main CLI group
@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version=__version__, prog_name='dotmatrix')
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
    '--extract',
    type=click.Path(path_type=Path),
    help='Extract circles to separate PNG images by color (directory path)'
)
@click.option(
    '--min-radius',
    type=int,
    default=10,
    help='Minimum circle radius in pixels (default: 10)'
)
@click.option(
    '--max-radius',
    type=int,
    default=500,
    help='Maximum circle radius in pixels (default: 500)'
)
@click.option(
    '--min-distance',
    type=int,
    default=20,
    help='Minimum distance between circle centers in pixels (default: 20)'
)
@click.option(
    '--color-tolerance',
    type=int,
    default=20,
    help='RGB distance threshold for color grouping (default: 20, range: 0-100)'
)
@click.option(
    '--max-colors',
    type=int,
    help='Maximum number of color groups using k-means clustering (only with --extract)'
)
@click.option(
    '--sensitivity',
    type=click.Choice(['strict', 'normal', 'relaxed'], case_sensitive=False),
    default='normal',
    help='Detection sensitivity preset (default: normal)'
)
@click.option(
    '--min-confidence',
    type=click.IntRange(0, 100),
    help='Minimum confidence score to include detection (0-100)'
)
@click.option(
    '--edge-sampling',
    is_flag=True,
    help='Use edge-based color sampling for better accuracy with overlapping circles'
)
@click.option(
    '--edge-samples',
    type=int,
    default=36,
    help='Number of sample points around circle edge for edge sampling (default: 36)'
)
@click.option(
    '--edge-method',
    type=click.Choice(['circumference', 'canny', 'exposed', 'band'], case_sensitive=False),
    default='circumference',
    help='Edge sampling method: circumference (default), canny (edge pixels), exposed (visible arcs), band (pixel band)'
)
@click.option(
    '--exclude-background',
    is_flag=True,
    help='Exclude near-white background colors (RGB > 240) from extraction'
)
@click.option(
    '--use-histogram',
    is_flag=True,
    help='Use histogram-based color palette extraction (recommended for CMYK)'
)
@click.option(
    '--color-separation',
    is_flag=True,
    help='Separate image by color first, then detect circles independently per color (best for overlapping)'
)
@click.option(
    '--convex-edge',
    is_flag=True,
    help='Use convex edge detection for heavily overlapping circles (best accuracy for CMYK/halftone)'
)
@click.option(
    '--palette',
    type=str,
    default='cmyk',
    help='Color palette for convex-edge mode: "auto" (detect from image), preset (cmyk, rgb), or custom "R,G,B;R,G,B" (default: cmyk)'
)
@click.option(
    '--num-colors',
    type=int,
    default=6,
    help='Number of colors to detect when using --palette auto (default: 6)'
)
@click.option(
    '--quantize-output',
    type=click.Path(path_type=Path),
    help='Save quantized image to this path (for debugging convex-edge mode)'
)
@click.option(
    '--run-name',
    type=str,
    help='Custom name for this run (creates named subdirectory in extract folder)'
)
@click.option(
    '--no-organize',
    is_flag=True,
    help='Disable automatic subdirectory creation for --extract (flat output)'
)
@click.option(
    '--save-config',
    type=click.Path(path_type=Path),
    help='Save current settings to config file (YAML or JSON)'
)
@click.option(
    '--no-manifest',
    is_flag=True,
    help='Disable automatic manifest.json generation when using --extract'
)
@click.option(
    '--chunk-size',
    type=str,
    default='auto',
    help='Tile size for chunked processing: "auto" (default), pixel size (e.g. "2000"), or "0" to disable'
)
def cli(ctx, config, input, output, format, debug, extract, min_radius, max_radius, min_distance, color_tolerance, max_colors, sensitivity, min_confidence, edge_sampling, edge_samples, edge_method, exclude_background, use_histogram, color_separation, convex_edge, palette, num_colors, quantize_output, run_name, no_organize, save_config, no_manifest, chunk_size):
    """DotMatrix: Detect circles in images.

    Identifies the center coordinates, radius, and color of circles in images,
    even when circles overlap.

    Example:
        dotmatrix --input image.png --format json
        dotmatrix --config config.json --input image.png

    Use 'dotmatrix runs' to list and manage past runs.
    """
    # If no subcommand invoked, run detect (for backward compatibility)
    if ctx.invoked_subcommand is None:
        _do_detect(config, input, output, format, debug, extract, min_radius, max_radius,
                   min_distance, color_tolerance, max_colors, sensitivity, min_confidence,
                   edge_sampling, edge_samples, edge_method, exclude_background, use_histogram,
                   color_separation, convex_edge, palette, num_colors, quantize_output, run_name,
                   no_organize, save_config, no_manifest, chunk_size)


def _do_detect(config, input, output, format, debug, extract, min_radius, max_radius, min_distance, color_tolerance, max_colors, sensitivity, min_confidence, edge_sampling, edge_samples, edge_method, exclude_background, use_histogram, color_separation, convex_edge, palette, num_colors, quantize_output, run_name, no_organize, save_config, no_manifest, chunk_size='auto'):
    """Internal function for circle detection."""
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

    # Validate required --input parameter
    if not input:
        click.echo("Error: --input is required (either via CLI or config file)", err=True)
        sys.exit(1)

    if debug:
        click.echo(f"Debug mode enabled", err=True)
        click.echo(f"Input: {input}", err=True)
        click.echo(f"Output: {output or 'stdout'}", err=True)
        click.echo(f"Format: {format}", err=True)

    # Validate --max-colors requires --extract
    if max_colors is not None and not extract:
        click.echo(
            "Error: --max-colors can only be used with --extract",
            err=True
        )
        sys.exit(1)

    # Validate file extension
    valid_extensions = {'.png', '.jpg', '.jpeg'}
    if input.suffix.lower() not in valid_extensions:
        click.echo(
            f"Error: Invalid file format '{input.suffix}'. "
            f"Supported formats: {', '.join(valid_extensions)}",
            err=True
        )
        sys.exit(1)

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
                process_chunked, calculate_chunk_size, PALETTES
            )

            # Show progress message for convex detection (can be slow for large images)
            if megapixels > 5:  # Show progress for images > 5 MP
                click.echo(f"Detecting circles (convex edge analysis)...", err=True)

            if debug:
                click.echo(f"Using convex edge detection with palette: {palette}", err=True)

            # Convert BGR to RGB for convex detector (needed for both auto and preset)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Handle auto-palette detection
            if palette.lower() == 'auto':
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

            if debug:
                click.echo(f"Palette colors: {len(color_palette)}", err=True)
                for i, color in enumerate(color_palette):
                    click.echo(f"  {i+1}. {get_color_name(color)} RGB{color}", err=True)

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
                    debug_callback=None
                )
                quantized = None  # Not available in chunked mode
            else:
                # Debug callback to show per-color progress
                def debug_cb(color, mask, circles):
                    if debug:
                        click.echo(f"  {get_color_name(color)}: {len(circles)} circle(s) detected", err=True)

                # Detect all circles using convex edge analysis
                detected_circles, quantized = detect_all_circles(
                    image_rgb,
                    color_palette,
                    min_radius=min_radius,
                    max_radius=max_radius,
                    exclude_background=True,
                    debug_callback=debug_cb if debug else None
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
            from .run_manager import create_run_directory

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

            extracted_files = extract_circles_to_images(
                results,
                image_shape=image.shape[:2],
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
                    source_file=input,
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

        # 5. Format output (skip if only extracting)
        if not extract or output or not extract:
            if format.lower() == 'json':
                formatted_output = format_json(results)
            else:  # csv
                formatted_output = format_csv(results)

            # 6. Write to output or stdout
            if output:
                output.write_text(formatted_output)
                if debug:
                    click.echo(f"Results written to: {output}", err=True)
            elif not extract:  # Only print to stdout if not extracting
                click.echo(formatted_output)

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
