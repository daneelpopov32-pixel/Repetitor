"""Research: extract actual task content with proper decoding."""
import asyncio
import httpx
from bs4 import BeautifulSoup
import re

BASE = "https://ege.fipi.ru/bank"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://ege.fipi.ru/bank/index.php?proj=068A227D253BA6C04D0C832387FD0D89",
}

async def fetch_page(client, theme=None, page=1, pagesize=10):
    """Fetch a page of questions, optionally filtered by theme."""
    url = f"{BASE}/questions.php"
    data = {
        "search": "1",
        "pagesize": str(pagesize),
        "proj": "068A227D253BA6C04D0C832387FD0D89",
        "page": str(page),
    }
    if theme:
        data["theme"] = theme
    resp = await client.post(url, data=data, headers=HEADERS)
    return resp.content.decode("windows-1251", errors="replace")

async def extract_tasks(html, max_tasks=3):
    """Extract task data from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    qblocks = soup.find_all("div", class_="qblock")
    tasks = []

    for qb in qblocks[:max_tasks]:
        task = {}

        # Get task ID
        task["block_id"] = qb.get("id", "").replace("q", "")

        # Get hint (task type description)
        hint = qb.find("div", class_="hint")
        if hint:
            task["hint"] = hint.get_text(strip=True)

        # Get form
        form = qb.find("form", id=lambda x: x and x.startswith("checkform"))
        if form:
            # Get GUID
            guid_input = form.find("input", {"name": "guid"})
            if guid_input:
                task["guid"] = guid_input.get("value", "")

            # Check for selects (matching tasks)
            selects = form.find_all("select")
            if selects:
                task["type"] = "MATCHING"
                task["num_selects"] = len(selects)
                # Get options for each select
                task["options"] = []
                for s in selects:
                    opts = []
                    for o in s.find_all("option"):
                        opts.append({"value": o.get("value", ""), "text": o.get_text(strip=True)})
                    task["options"].append(opts)
            else:
                # Check for text inputs
                text_inputs = form.find_all("input", type="text")
                if text_inputs:
                    task["type"] = "SHORT_ANSWER"
                else:
                    task["type"] = "ESSAY_OR_UNKNOWN"

        # Get task text from the table
        # The text is in a table with cell_0 class
        cell = qb.find("td", class_="cell_0")
        if cell:
            # Get all text content
            task["text"] = cell.get_text(separator=" ", strip=True)[:500]

            # Get images
            images = cell.find_all("img")
            task["images"] = []
            for img in images:
                src = img.get("src", "")
                if src:
                    task["images"].append(src)

        tasks.append(task)

    return tasks

async def research():
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, verify=False) as client:
        # Test with theme 1 (Древний мир)
        print("=== FETCHING THEME 1 ===")
        html = await fetch_page(client, theme="1.", page=1, pagesize=5)
        tasks = await extract_tasks(html, max_tasks=5)

        for i, t in enumerate(tasks):
            print(f"\n--- Task {i+1} ---")
            print(f"  ID: {t.get('block_id')}")
            print(f"  GUID: {t.get('guid', 'N/A')[:20]}...")
            print(f"  Type: {t.get('type')}")
            print(f"  Hint: {t.get('hint', 'N/A')[:100]}")
            print(f"  Text: {t.get('text', 'N/A')[:300]}")
            if t.get("images"):
                print(f"  Images: {t['images'][:3]}")
            if t.get("options"):
                print(f"  Options: {len(t['options'])} selects")
                for j, opts in enumerate(t["options"][:2]):
                    print(f"    Select {j}: {len(opts)} options")

        # Check how many total pages
        print("\n\n=== PAGINATION CHECK ===")
        html_full = await fetch_page(client, theme="1.", page=1, pagesize=100)
        soup = BeautifulSoup(html_full, "html.parser")
        qblocks_all = soup.find_all("div", class_="qblock")
        print(f"Theme 1 with pagesize=100: {len(qblocks_all)} qblocks")

        # Check the setQCount in scripts
        for script in soup.find_all("script", src=False):
            text = script.get_text(strip=True)
            match = re.search(r'setQCount\((\d+)', text)
            if match:
                print(f"Total questions for theme 1: {match.group(1)}")

        # Try theme 8.1
        print("\n=== THEME 8.1 ===")
        html_81 = await fetch_page(client, theme="8.1.", page=1, pagesize=5)
        tasks_81 = await extract_tasks(html_81, max_tasks=3)
        for t in tasks_81:
            print(f"  ID: {t.get('block_id')}, Type: {t.get('type')}, Text: {t.get('text', 'N/A')[:150]}")

asyncio.run(research())
