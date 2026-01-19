"""
Project path utilities.
"""

from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).parent.parent

# Media directory
MEDIA_ROOT = BASE_DIR / "media"

# Assets directory
ASSETS_ROOT = BASE_DIR / "assets"

# Static files directory
STATIC_ROOT = ASSETS_ROOT / "static"

# Templates directory
TEMPLATES_ROOT = ASSETS_ROOT / "template"
