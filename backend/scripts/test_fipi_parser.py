"""Test parser on a few themes."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://repetitor:repetitor@localhost:5432/repetitor")

from scripts.fipi_parser import fetch_page, extract_tasks_from_html, THEME_NAMES
import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://ege.fipi.ru/bank/index.php?proj=068A227D253BA6C04D0C832387FD0D89",
}

async def test_parser():
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, verify=False) as client:
        # Test on themes 1, 7, 8 (which have variety of task types)
        test_themes = ["1.", "7.", "8."]

        total_tasks = 0
        type_counts = {"TEST": 0, "ESSAY": 0}

        for theme_code in test_themes:
            theme_name = THEME_NAMES.get(theme_code, "Unknown")
            print(f"\n=== Theme {theme_code} ({theme_name}) ===")

            html = await fetch_page(client, theme=theme_code, page=1, pagesize=50)
            tasks = extract_tasks_from_html(html)

            print(f"  Found {len(tasks)} tasks")

            for t in tasks[:3]:  # Show first 3
                print(f"\n  --- Task ---")
                print(f"    ID: {t.get('block_id')}")
                print(f"    GUID: {t.get('guid', 'N/A')[:20]}...")
                print(f"    Type: {t.get('type')}")
                print(f"    Subtype: {t.get('subtype')}")
                print(f"    Hint: {t.get('hint', 'N/A')[:80]}")
                text = t.get('text', 'N/A')
                print(f"    Text: {text[:200]}...")
                if t.get('images'):
                    print(f"    Images: {len(t['images'])}")
                if t.get('options'):
                    print(f"    Options: {len(t['options'])} selects")
                    for i, opts in enumerate(t['options'][:2]):
                        print(f"      Select {i}: {len(opts)} options")

            total_tasks += len(tasks)
            for t in tasks:
                task_type = t.get("type", "TEST")
                type_counts[task_type] = type_counts.get(task_type, 0) + 1

            await asyncio.sleep(1.5)

        print(f"\n=== SUMMARY ===")
        print(f"Total tasks: {total_tasks}")
        print(f"By type: {type_counts}")

asyncio.run(test_parser())
