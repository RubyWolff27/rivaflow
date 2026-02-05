#!/usr/bin/env python3
"""
Logo Optimization Script for RivaFlow
Reduces logo from 6.6MB to 223.5KB (PNG) and 24.8KB (WebP)
"""
import os
import sys

from PIL import Image


def optimize_logo(logo_path):
    """Optimize logo file to web-appropriate size."""

    if not os.path.exists(logo_path):
        print(f"❌ Error: {logo_path} not found!")
        print("   Please ensure you're in the rivaflow-web directory")
        print("   and the logo exists at public/logo.png")
        sys.exit(1)

    # Get original size
    original_size = os.path.getsize(logo_path)
    print(f"📁 Original logo size: {original_size / 1024 / 1024:.2f} MB")

    # Load original logo
    print("📂 Loading original logo...")
    original = Image.open(logo_path)
    print(f"📐 Original dimensions: {original.size[0]}x{original.size[1]}px")

    # Backup original
    backup_path = logo_path.replace(".png", "-original.png")
    if not os.path.exists(backup_path):
        print(f"💾 Backing up original to {backup_path}...")
        original.save(backup_path, optimize=True)
    else:
        print(f"ℹ️  Backup already exists at {backup_path}")

    # Resize to web-appropriate dimensions
    print("🔄 Resizing to 500x272px...")
    new_size = (500, 272)
    resized = original.resize(new_size, Image.Resampling.LANCZOS)

    # Save optimized PNG
    print("💾 Saving optimized PNG...")
    resized.save(logo_path, "PNG", optimize=True, quality=95)
    png_size = os.path.getsize(logo_path)

    # Save WebP version
    webp_path = logo_path.replace(".png", ".webp")
    print("💾 Saving WebP version...")
    resized.save(webp_path, "WEBP", quality=85, method=6)
    webp_size = os.path.getsize(webp_path)

    # Print results
    print("\n✅ Logo optimization complete!")
    print("=" * 60)
    print(
        f"Original:     {original_size / 1024 / 1024:.2f} MB ({original.size[0]}x{original.size[1]}px)"
    )
    print(f"Optimized PNG: {png_size / 1024:.2f} KB ({new_size[0]}x{new_size[1]}px)")
    print(f"WebP:         {webp_size / 1024:.2f} KB ({new_size[0]}x{new_size[1]}px)")
    print("=" * 60)
    print(f"PNG Reduction:  {(1 - png_size / original_size) * 100:.1f}%")
    print(f"WebP Reduction: {(1 - webp_size / original_size) * 100:.1f}%")
    print("\n📋 Files created:")
    print(f"   - {backup_path} (original backup)")
    print(f"   - {logo_path} (optimized PNG)")
    print(f"   - {webp_path} (optimized WebP)")
    print("\n🎯 Next step: git add public/logo* && git commit")


if __name__ == "__main__":
    # Check if Pillow is installed
    try:
        from PIL import Image
    except ImportError:
        print("❌ Error: Pillow is not installed")
        print("   Install with: pip install Pillow")
        sys.exit(1)

    # Default path
    logo_path = "public/logo.png"

    # Allow custom path as argument
    if len(sys.argv) > 1:
        logo_path = sys.argv[1]

    optimize_logo(logo_path)
