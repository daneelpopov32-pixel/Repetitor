"""Research: trace the full check cycle with crtm token."""
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

async def research():
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, verify=False) as client:
        # First fetch the main page to get cookies and crtm
        main_url = f"{BASE}/index.php?proj=068A227D253BA6C04D0C832387FD0D89"
        resp = await client.get(main_url, headers=HEADERS)
        html_main = resp.content.decode("windows-1251", errors="replace")

        # Find crtm in main page
        match = re.search(r'var crtm="(\d+)"', html_main)
        if match:
            crtm_main = match.group(1)
            print(f"CRTM from main page: {crtm_main}")

        # Now fetch the questions page
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

        # Find crtm in questions page
        for script in soup.find_all("script", src=False):
            text = script.get_text(strip=True)
            match = re.search(r'var crtm="(\d+)"', text)
            if match:
                crtm_q = match.group(1)
                print(f"CRTM from questions page: {crtm_q}")

        # Get the form
        form = soup.find("form", id=lambda x: x and x.startswith("checkform"))
        if form:
            form_id = form.get("id", "")
            guid = form.find("input", {"name": "guid"}).get("value", "")
            print(f"Form: {form_id}, GUID: {guid}")

            # Try to check with crtm token
            for answer in ["012", "123", "000"]:
                check_data = {
                    "guid": guid,
                    "answer": answer,
                    "chkcode": "",
                    "crtm": crtm_q,
                }
                check_resp = await client.post(f"{BASE}/questions.php", data=check_data, headers=HEADERS)
                print(f"\nAnswer '{answer}': status={check_resp.status_code}, length={len(check_resp.text)}")
                print(f"  Content: {check_resp.text[:300]}")

        # Also check the checkButtonClick function in the page
        print("\n=== checkButtonClick in page ===")
        for script in soup.find_all("script", src=False):
            text = script.get_text(strip=True)
            if "checkButtonClick" in text:
                # Find the function definition
                idx = text.find("function checkButtonClick")
                if idx >= 0:
                    print(text[idx:idx+1000])
                break

asyncio.run(research())
