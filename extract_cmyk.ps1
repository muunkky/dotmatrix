# Extract CMYK overlapping circles using optimized config

param(
    [Parameter(Mandatory=$true, HelpMessage="Input image file path")]
    [string]$Input,

    [Parameter(HelpMessage="Output directory (default: output)")]
    [string]$Output = "output",

    [Parameter(HelpMessage="Config file (default: configs/cmyk-overlapping.json)")]
    [string]$Config = "configs/cmyk-overlapping.json",

    [Parameter(HelpMessage="Override max colors (default: 4 from config)")]
    [int]$MaxColors,

    [Parameter(HelpMessage="Enable debug output")]
    [switch]$Debug
)

# Show help if no parameters
if ($Help) {
    Write-Host @"
Extract CMYK overlapping circles from an image using optimized detection parameters.

Usage: .\extract_cmyk.ps1 -Input IMAGE [OPTIONS]

Required:
  -Input IMAGE          Input image file path

Optional:
  -Output DIR           Output directory (default: output)
  -Config FILE          Config file (default: configs/cmyk-overlapping.json)
  -MaxColors N          Override max colors (default: 4 from config)
  -Debug                Enable debug output

Examples:
  .\extract_cmyk.ps1 -Input test_dotmatrix.png
  .\extract_cmyk.ps1 -Input image.png -Output results\ -Debug
  .\extract_cmyk.ps1 -Input image.png -MaxColors 5

"@
    exit 0
}

# Validate input file
if (-not (Test-Path $Input)) {
    Write-Error "Input file not found: $Input"
    exit 1
}

# Validate config file
if (-not (Test-Path $Config)) {
    Write-Error "Config file not found: $Config"
    exit 1
}

# Build command
$cmd = "python -m dotmatrix --config `"$Config`" --input `"$Input`" --extract `"$Output`""

if ($MaxColors) {
    $cmd += " --max-colors $MaxColors"
}

if ($Debug) {
    $cmd += " --debug"
}

# Run the command
Write-Host "Extracting CMYK circles from: $Input"
Write-Host "Output directory: $Output"
Write-Host ""

Invoke-Expression $cmd

Write-Host ""
Write-Host "Done! Check $Output\ for extracted color groups."
