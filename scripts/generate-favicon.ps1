# Generate favicon.ico from favicon.svg
# This script creates a minimal valid ICO file from the SVG design

$svgPath = "..\frontend\public\favicon.svg"
$icoPath = "..\backend\static\favicon.ico"

# Read the SVG content
$svgContent = Get-Content $svgPath -Raw

# Create a minimal valid ICO file
# ICO format: 6-byte header + 16-byte directory entry + PNG data
$icoDir = [System.IO.BinaryWriter]::new([System.IO.File]::Open($icoPath, [System.IO.FileMode]::Create))

# ICONDIR header (6 bytes)
$icoDir.Write([UInt16]::new(0))  # Reserved (must be 0)
$icoDir.Write([UInt16]::new(1))  # Type: 1 = ICO
$icoDir.Write([UInt16]::new(1))  # Number of images: 1

# ICONDIRENTRY (16 bytes)
$icoDir.Write([Byte]::new(64))   # Width (64 pixels)
$icoDir.Write([Byte]::new(64))   # Height (64 pixels)
$icoDir.Write([Byte]::new(0))    # Color palette (0 = no palette)
$icoDir.Write([Byte]::new(0))    # Reserved
$icoDir.Write([UInt16]::new(1))  # Color planes
$icoDir.Write([UInt16]::new(32)) # Bits per pixel
$icoDir.Write([UInt32]::new(0))  # Size of image data (placeholder)
$icoDir.Write([UInt32]::new(22)) # Offset to image data (6 + 16 = 22)

# For now, create a minimal 1x1 transparent PNG as placeholder
# In production, use an online converter or ImageMagick to convert SVG to ICO
$pngData = [Convert]::FromBase64String(
    "iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH5QMWESo1y0fvjQAAAFZJREFUeNrtwTEBAAAAwqD1T20JT6AAAH4AAAAAAAD4AAAAAAB4AAAAAAAB4AAAAAAAD4AAAAAAB4AAAAAAAB4AAAAAAAD4AAAAAAB4AAAAAAAB4AAAAAAB4P4HAAQYA0Rj4S7AAAAAElFTkSuQmCC"
)

# Update the size field
$icoDir.Seek(22, [System.IO.SeekOrigin]::Begin)
$icoDir.Write([UInt32]::new($pngData.Length))

# Write PNG data
$icoDir.Write($pngData, 0, $pngData.Length)
$icoDir.Close()

Write-Host "Created $icoPath" -ForegroundColor Green
Write-Host "NOTE: This is a placeholder. For production, convert favicon.svg to ICO using:" -ForegroundColor Yellow
Write-Host "  - Online: https://convertio.co/svg-ico/" -ForegroundColor Yellow
Write-Host "  - ImageMagick: magick convert favicon.svg favicon.ico" -ForegroundColor Yellow
Write-Host "  - Inkscape: inkscape --export-type=ico --export-filename=favicon.ico favicon.svg" -ForegroundColor Yellow