"""Research: check the AJAX response content."""
import asyncio
import httpx
from bs4 import BeautifulSoup

BASE = "https://ege.fipi.ru/bank"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://ege.fipi.ru/bank/index.php?proj=068A227D253BA6C04D0C832387FD0D89",
}

async def research():
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, verify=False) as client:
        # Fetch a page
        url = f"{BASE}/questions.php"
        data = {
            "search": "1",
            "pagesize": "5",
            "proj": "068A227D253BA6C04D0C832387FD0D89",
            "theme": "1.",
            "page": "1",
        }
        resp = await client.post(url, data=data, headers=HEADERS)
        html = resp.content.decode("windows-1251", errors="replace")
        soup = BeautifulSoup(html, "html.parser")

        # Get the first form
        form = soup.find("form", id=lambda x: x and x.startswith("checkform"))
        if form:
            form_id = form.get("id", "")
            guid = form.find("input", {"name": "guid"}).get("value", "")

            print(f"Form: {form_id}, GUID: {guid}")

            # Try to submit the form via AJAX with different answer values
            for answer in ["0000", "1234", "1111", "0000000"]:
                check_data = {
                    "guid": guid,
                    "answer": answer,
                    "chkcode": "",
                }
                check_resp = await client.post(f"{BASE}/questions.php", data=check_data, headers=HEADERS)
                print(f"\nAnswer '{answer}': status={check_resp.status_code}, length={len(check_resp.text)}")
                print(f"  Content-Type: {check_resp.headers.get('content-type', 'unknown')}")
                print(f"  Raw bytes: {check_resp.content[:200]}")
                print(f"  Text: {check_resp.text[:200]}")

        # Also check the full t3utils.js for checkButtonClick
        print("\n=== FULL t3utils.js search ===")
        js_url = f"{BASE}/../lib/t3utils.js?v=2.04"
        resp = await client.get(js_url, headers=HEADERS)
        js_text = resp.text

        # Search for checkButtonClick
        idx = js_text.find("checkButtonClick")
        if idx >= 0:
            print(f"Found 'checkButtonClick' at position {idx}")
            print(js_text[max(0, idx-200):idx+1000])
        else:
            print("'checkButtonClick' not found in t3utils.js")

        # Search for all function definitions
        print("\n=== Function definitions in t3utils.js ===")
        for match in re.finditer(r'function\s+(\w+)', js_text):
            print(f"  {match.group(1)}")

        # Check the bdetect.js
        print("\n=== bdetect.js ===")
        bd_url = f"{BASE}/../lib/bdetect.js"
        resp = await client.get(bd_url, headers=HEADERS)
        print(f"Status: {resp.status_code}, Length: {len(resp.text)}")
        print(resp.text[:500])

import re
asyncio.run(research())
