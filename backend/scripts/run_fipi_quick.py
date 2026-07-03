"""Run parser on first 5 themes for quick validation."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://repetitor:repetitor@localhost:5432/repetitor")

from scripts.fipi_parser import parse_fipi_history
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Override to only parse first 5 themes
import scripts.fipi_parser as fp
original_themes = fp.THEME_NAMES
fp.THEME_NAMES = dict(list(original_themes.items())[:5])

asyncio.run(parse_fipi_history())
