"""Research: understand answer reveal mechanism."""
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

async def research():
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, verify=False) as client:
        html = await fetch_page(client, theme="1.", page=1, pagesize=5)
        soup = BeautifulSoup(html, "html.parser")

        # Find the answer-button elements and their context
        answer_buttons = soup.find_all("span", class_="answer-button")
        print(f"Found {len(answer_buttons)} answer buttons\n")

        for i, btn in enumerate(answer_buttons[:3]):
            print(f"=== Answer Button {i+1} ===")
            # Get the parent qblock
            qblock = btn.find_parent("div", class_="qblock")
            if qblock:
                qid = qblock.get("id", "")
                print(f"  QBlock ID: {qid}")

                # Get the form
                form = qblock.find("form", id=lambda x: x and x.startswith("checkform"))
                if form:
                    guid = form.find("input", {"name": "guid"})
                    print(f"  GUID: {guid.get('value', '') if guid else 'N/A'}")

            # Get the onclick or data attributes
            print(f"  Button HTML: {str(btn)[:300]}")
            print(f"  Button text: {btn.get_text(strip=True)}")
            print(f"  onclick: {btn.get('onclick', 'N/A')}")
            print(f"  data-*: {[(k, v) for k, v in btn.attrs.items() if k.startswith('data-')]}")
            print()

        # Look for the t3utils.js script to understand answer checking
        print("=== CHECKING t3utils.js ===")
        script_url = f"{BASE}/../lib/t3utils.js?v=2.04"
        resp = await client.get(script_url, headers=HEADERS)
        if resp.status_code == 200:
            js_text = resp.text
            # Search for answer-related functions
            for func_name in ["checkAnswer", "showAnswer", "verifyAnswer", "getAnswer", "Answer"]:
                idx = js_text.find(func_name)
                if idx >= 0:
                    # Get surrounding context
                    start = max(0, idx - 100)
                    end = min(len(js_text), idx + 500)
                    print(f"\n  Found '{func_name}' at position {idx}:")
                    print(f"  {js_text[start:end]}")
                    print()

        # Look for the verify/check AJAX call
        print("\n=== AJAX CHECK MECHANISM ===")
        # Find the form submission handler
        for script in soup.find_all("script", src=False):
            text = script.get_text(strip=True)
            if "check" in text.lower() and ("form" in text.lower() or "submit" in text.lower()):
                # Look for the actual check logic
                lines = text.split("\n")
                for line in lines:
                    if "check" in line.lower() or "submit" in line.lower() or "verify" in line.lower():
                        print(f"  {line.strip()[:200]}")

asyncio.run(research())
