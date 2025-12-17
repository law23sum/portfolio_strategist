#!/usr/bin/env python3
"""
Generate placeholder PNG icons for iOS app.
This script creates simple placeholder icons that can be replaced with proper designs later.
"""

import os

from PIL import Image, ImageDraw, ImageFont

# Icon definitions with sizes
ICONS = {
    # Tab bar icons - 25x25 points (50x50 @2x, 75x75 @3x)
    "icon-dashboard": {"size": 25, "text": "D"},
    "icon-records": {"size": 25, "text": "R"},
    "icon-stocks": {"size": 25, "text": "S"},
    "icon-solutions": {"size": 25, "text": "L"},
    "icon-chat": {"size": 25, "text": "C"},
    "icon-profile": {"size": 25, "text": "P"},
    # Dashboard icons - 32x32 points (64x64 @2x, 96x96 @3x)
    "icon-upload": {"size": 32, "text": "↑"},
    "icon-analyze-stock": {"size": 32, "text": "📈"},
    "icon-link-account": {"size": 32, "text": "🔗"},
    "icon-insights": {"size": 32, "text": "💡"},
    "icon-attach-money": {"size": 32, "text": "$"},
    "icon-wallet": {"size": 32, "text": "💳"},
    "icon-credit-card": {"size": 32, "text": "💳"},
    "icon-arrow-up": {"size": 32, "text": "↑"},
    "icon-arrow-down": {"size": 32, "text": "↓"},
    # Records icons - 32x32 points
    "icon-explorer": {"size": 32, "text": "🔍"},
    "icon-linked-accounts": {"size": 32, "text": "🔗"},
    "icon-description": {"size": 32, "text": "📄"},
    "icon-camera": {"size": 32, "text": "📷"},
    # Stock analysis icons - 32x32 points
    "icon-search": {"size": 32, "text": "🔍"},
    "icon-account-balance": {"size": 32, "text": "🏦"},
    "icon-info": {"size": 32, "text": "ℹ️"},
    "icon-loan-analysis": {"size": 32, "text": "💰"},
    # Chat icons - 24x24 points (48x48 @2x, 72x72 @3x)
    "icon-person": {"size": 24, "text": "👤"},
    "icon-smart-toy": {"size": 24, "text": "🤖"},
    "icon-arrow-back": {"size": 24, "text": "←"},
    "icon-delete": {"size": 24, "text": "🗑"},
    "icon-send": {"size": 24, "text": "➤"},
    # Common UI icons - 24x24 points
    "icon-chevron-right": {"size": 24, "text": "›"},
    "icon-edit": {"size": 24, "text": "✎"},
    "icon-lock": {"size": 24, "text": "🔒"},
    "icon-notifications": {"size": 24, "text": "🔔"},
    "icon-subscriptions": {"size": 24, "text": "📋"},
    "icon-privacy": {"size": 24, "text": "🔐"},
    "icon-help": {"size": 24, "text": "?"},
    "icon-logout": {"size": 24, "text": "↪"},
    "icon-add": {"size": 24, "text": "+"},
    "icon-sync": {"size": 24, "text": "↻"},
    "icon-link-off": {"size": 24, "text": "🔗"},
    "icon-savings": {"size": 24, "text": "💰"},
    "icon-download": {"size": 24, "text": "↓"},
}


def create_icon_image(icon_name, size_pt, text, scale):
    """Create a PNG image for an icon at a specific scale."""
    # Calculate pixel size (points * scale)
    pixel_size = int(size_pt * scale)

    # Create image with transparent background
    img = Image.new("RGBA", (pixel_size, pixel_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Try to use a font, fallback to default if not available
    try:
        # Try to use system font
        font_size = int(pixel_size * 0.6)
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", int(pixel_size * 0.6))
        except Exception:
            font = ImageFont.load_default()

    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center the text
    x = (pixel_size - text_width) / 2
    y = (pixel_size - text_height) / 2 - bbox[1]

    # Draw text in dark gray
    draw.text((x, y), text, fill=(50, 50, 50, 255), font=font)

    return img


def generate_all_icons():
    """Generate all icon images."""
    base_dir = os.path.dirname(os.path.abspath(__file__))

    for icon_name, config in ICONS.items():
        icon_dir = os.path.join(base_dir, f"{icon_name}.imageset")

        # Ensure directory exists
        os.makedirs(icon_dir, exist_ok=True)

        # Generate @2x version
        img_2x = create_icon_image(icon_name, config["size"], config["text"], 2)
        img_2x.save(os.path.join(icon_dir, f"{icon_name}@2x.png"), "PNG")
        print(f"Generated {icon_name}@2x.png")

        # Generate @3x version
        img_3x = create_icon_image(icon_name, config["size"], config["text"], 3)
        img_3x.save(os.path.join(icon_dir, f"{icon_name}@3x.png"), "PNG")
        print(f"Generated {icon_name}@3x.png")

    print(f"\n✅ Generated {len(ICONS)} icon sets ({len(ICONS) * 2} PNG files total)")


if __name__ == "__main__":
    try:
        generate_all_icons()
    except ImportError:
        print("ERROR: PIL (Pillow) is required to generate icons.")
        print("Install it with: pip install Pillow")
        print("\nAlternatively, you can:")
        print("1. Use an online icon generator")
        print("2. Export icons from Material Design Icons (https://fonts.google.com/icons)")
        print("3. Use design tools like Figma, Sketch, or Adobe Illustrator")
    except Exception as e:
        print(f"Error generating icons: {e}")
        import traceback

        traceback.print_exc()
