"""Research: try solve.php endpoint."""
import asyncio
import httpx
from bs4 import BeautifulSoup
import re

BASE = "https://ege.fipi.ru/bank"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://ege.fipi.ru/bank/questions.php?proj=068A227D253BA6C04D0C832387FD0D89&init_filter_themes=1",
}

async def research():
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, verify=False) as client:
        # Fetch the questions page first to establish session
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

        # Get the form
        form = soup.find("form", id=lambda x: x and x.startswith("checkform"))
        if form:
            form_id = form.get("id", "")
            guid = form.find("input", {"name": "guid"}).get("value", "")
            print(f"Form: {form_id}, GUID: {guid}")

            # Get all select values to understand the answer format
            selects = form.find_all("select")
            print(f"Selects: {len(selects)}")
            for s in selects:
                name = s.get("name", "")
                options = s.find_all("option")
                print(f"  {name}: {[o.get('value') for o in options]}")

            # Try to check via solve.php
            for answer in ["012", "123", "000", "321"]:
                check_data = {
                    "guid": guid,
                    "answer": answer,
                    "ajax": "1",
                    "proj": "068A227D253BA6C04D0C832387FD0D89",
                }
                check_resp = await client.post(f"{BASE}/solve.php", data=check_data, headers=HEADERS)
                print(f"\nAnswer '{answer}': status={check_resp.status_code}, length={len(check_resp.text)}")
                print(f"  Content: {check_resp.text[:200]}")

            # Also try with chkcode
            print("\n=== With chkcode ===")
            check_data = {
                "guid": guid,
                "answer": "012",
                "chkcode": "",
                "ajax": "1",
                "proj": "068A227D253BA6C04D0C832387FD0D89",
            }
            check_resp = await client.post(f"{BASE}/solve.php", data=check_data, headers=HEADERS)
            print(f"Status: {check_resp.status_code}, Length: {len(check_resp.text)}")
            print(f"Content: {check_resp.text[:500]}")

asyncio.run(research())
