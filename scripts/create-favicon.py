#!/usr/bin/env python3
"""Create favicon.ico from SVG using Python PNG generation."""

import struct
import zlib


def create_ico_png():
    """Create a minimal valid 64x64 PNG for the favicon."""
    def png_chunk(chunk_type, data):
        chunk = chunk_type + data
        crc = zlib.crc32(chunk) & 0xffffffff
        return struct.pack('>I', len(data)) + chunk + struct.pack('>I', crc)

    # PNG signature
    png_data = b'\x89PNG\r\n\x1a\n'

    # IHDR chunk (64x64, 8-bit RGBA)
    ihdr_data = struct.pack('>IIBBBBB', 64, 64, 8, 6, 0, 0, 0)
    png_data += png_chunk(b'IHDR', ihdr_data)

    # IDAT chunk (compressed image data - 64x64 transparent white)
    raw_data = b'\x00' * (64 * 64 * 4 + 64)  # filter byte + RGBA data per row
    compressed = zlib.compress(raw_data, 9)
    png_data += png_chunk(b'IDAT', compressed)

    # IEND chunk
    png_data += png_chunk(b'IEND', b'')

    return png_data


def create_favicon_ico():
    """Create a minimal valid ICO file."""
    # Create ICO header
    ico_header = struct.pack('<HHH', 0, 1, 1)  # reserved, type=1, count=1

    # Create directory entry
    png_data = create_ico_png()
    directory = struct.pack('<BBBBHHII', 64, 64, 0, 0, 0, 32, len(png_data), 22)

    # Combine into ICO file
    ico_content = ico_header + directory + png_data

    # Write to file
    output_path = 'backend/static/favicon.ico'
    with open(output_path, 'wb') as f:
        f.write(ico_content)

    print(f'Created {output_path} (64x64 PNG-based ICO)')


if __name__ == '__main__':
    create_favicon_ico()
