#!/usr/bin/env python
"""
Script to verify templates can be found by Django
Run this inside the Docker container to debug template loading issues
"""

import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio_strategist.settings")
django.setup()

from django.conf import settings  # noqa: E402
from django.template.loader import get_template  # noqa: E402

print("=" * 60)
print("Django Template Loading Debug")
print("=" * 60)

print(f"\nBASE_DIR: {settings.BASE_DIR}")
print(f"TEMPLATES DIRS: {settings.TEMPLATES[0]['DIRS']}")
print(f"DEBUG: {settings.DEBUG}")

# Check if template directories exist
for template_dir in settings.TEMPLATES[0]["DIRS"]:
    print(f"\nChecking template directory: {template_dir}")
    if template_dir.exists():
        print("  ✓ Directory exists")
        web_dir = template_dir / "web"
        if web_dir.exists():
            print("  ✓ web/ subdirectory exists")
            template_file = web_dir / "savings_assessment.html"
            if template_file.exists():
                print("  ✓ savings_assessment.html exists")
                print(f"    Size: {template_file.stat().st_size} bytes")
            else:
                print("  ✗ savings_assessment.html NOT FOUND")
                print(f"    Looking for: {template_file}")
                print(f"    Files in web/: {list(web_dir.glob('*.html'))[:10]}")
        else:
            print("  ✗ web/ subdirectory NOT FOUND")
    else:
        print("  ✗ Directory does NOT exist")

# Try to load the template
print("\n" + "=" * 60)
print("Attempting to load template: web/savings_assessment.html")
print("=" * 60)
try:
    template = get_template("web/savings_assessment.html")
    print("✓ Template loaded successfully!")
    print(f"  Template object: {template}")
    print(f"  Origin: {template.origin}")
except Exception as e:
    print(f"✗ Failed to load template: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 60)
print("Checking other assessment templates")
print("=" * 60)
for template_name in ["web/stocks_assessment.html", "web/cd_assessment.html", "web/bond_assessment.html"]:
    try:
        template = get_template(template_name)
        print(f"✓ {template_name} - OK")
    except Exception as e:
        print(f"✗ {template_name} - FAILED: {e}")
