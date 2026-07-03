"""Research: find ESSAY tasks and check for answers."""
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

async def fetch_page(client, theme=None, page=1, pagesize=100):
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
        # Check different themes for variety of task types
        themes = ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.", "11.", "12."]

        for theme in themes:
            html = await fetch_page(client, theme=theme, page=1, pagesize=50)
            soup = BeautifulSoup(html, "html.parser")
            qblocks = soup.find_all("div", class_="qblock")

            # Count task types
            matching = 0
            short_answer = 0
            essay = 0
            for qb in qblocks:
                form = qb.find("form", id=lambda x: x and x.startswith("checkform"))
                if form:
                    selects = form.find_all("select")
                    text_inputs = form.find_all("input", type="text")
                    if selects:
                        matching += 1
                    elif text_inputs:
                        short_answer += 1
                    else:
                        essay += 1

            print(f"Theme {theme}: {len(qblocks)} tasks - matching={matching}, short_answer={short_answer}, essay={essay}")

        # Now look for answer reveal mechanism
        print("\n=== ANSWER REVEAL ===")
        html = await fetch_page(client, theme="1.", page=1, pagesize=10)
        soup = BeautifulSoup(html, "html.parser")

        # Look for "show answer" buttons or links
        for el in soup.find_all(["button", "a", "span"], class_=lambda c: c and any(k in str(c).lower() for k in ["answer", "show", "reveal", "check"])):
            print(f"  Found: tag={el.name} class={el.get('class')} text={el.get_text(strip=True)[:50]}")

        # Look for answer-related JavaScript
        for script in soup.find_all("script", src=False):
            text = script.get_text(strip=True)
            if "answer" in text.lower() and ("show" in text.lower() or "check" in text.lower() or "verify" in text.lower()):
                print(f"  JS with answer: {text[:300]}")

        # Check if there's an AJAX endpoint for checking answers
        print("\n=== AJAX ENDPOINTS ===")
        for script in soup.find_all("script", src=False):
            text = script.get_text(strip=True)
            if "ajax" in text.lower() or "xmlhttp" in text.lower() or "fetch" in text.lower():
                print(f"  AJAX script: {text[:500]}")

        # Look at the verify/check mechanism
        print("\n=== VERIFY FORMS ===")
        verify_forms = soup.find_all("form", id=lambda x: x and "verify" in str(x).lower())
        print(f"  Found {len(verify_forms)} verify forms")

        # Check for the answer panel content
        answer_panels = soup.find_all("div", class_="answer-panel")
        for ap in answer_panels[:3]:
            print(f"  Answer panel: {ap.get_text(strip=True)[:200]}")
            # Check for hidden elements
            for hidden in ap.find_all(["input", "div"], style=lambda s: s and "display:none" in str(s).lower()):
                print(f"    Hidden: {hidden.get_text(strip=True)[:100]}")

asyncio.run(research())
