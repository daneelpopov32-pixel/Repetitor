"""Research: trace the full AJAX answer check cycle."""
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
        # First fetch the t3utils.js to understand the full check mechanism
        js_url = f"{BASE}/../lib/t3utils.js?v=2.04"
        resp = await client.get(js_url, headers=HEADERS)
        js_text = resp.text

        # Find the checkButtonClick function
        print("=== checkButtonClick function ===")
        idx = js_text.find("function checkButtonClick")
        if idx >= 0:
            # Get the full function
            depth = 0
            start = idx
            for i in range(idx, min(idx + 2000, len(js_text))):
                if js_text[i] == '{':
                    depth += 1
                elif js_text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        print(js_text[start:i+1])
                        break

        # Find the checkSolutionDone function
        print("\n=== checkSolutionDone function ===")
        idx = js_text.find("function checkSolutionDone")
        if idx >= 0:
            depth = 0
            start = idx
            for i in range(idx, min(idx + 2000, len(js_text))):
                if js_text[i] == '{':
                    depth += 1
                elif js_text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        print(js_text[start:i+1])
                        break

        # Find the onButtonClick function (the main check handler)
        print("\n=== onButtonClick function ===")
        # Look in the page HTML
        url = f"{BASE}/questions.php?proj=068A227D253BA6C04D0C832387FD0D89&init_filter_themes=1"
        resp = await client.get(url, headers=HEADERS)
        html = resp.content.decode("windows-1251", errors="replace")

        for script in BeautifulSoup(html, "html.parser").find_all("script", src=False):
            text = script.get_text(strip=True)
            if "onButtonClick" in text and "checkform" in text:
                print(text[:1000])
                break

        # Now try to actually check an answer via AJAX
        print("\n=== TRYING AJAX ANSWER CHECK ===")
        # Fetch a page with a specific task
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

            # Try to submit the form via AJAX
            # The form action is "javascript:noAction()" so we need to POST to questions.php
            check_data = {
                "guid": guid,
                "answer": "0000",  # Dummy answer
                "chkcode": "",
            }

            # Try POST to questions.php
            check_url = f"{BASE}/questions.php"
            check_resp = await client.post(check_url, data=check_data, headers=HEADERS)
            check_html = check_resp.content.decode("windows-1251", errors="replace")
            print(f"\nAJAX response status: {check_resp.status_code}")
            print(f"Response length: {len(check_html)}")

            # Look for answer-related content
            check_soup = BeautifulSoup(check_html, "html.parser")
            answer_divs = check_soup.find_all("div", class_="answer-panel")
            for ad in answer_divs[:2]:
                print(f"Answer panel: {ad.get_text(strip=True)[:200]}")

            # Check if there's an answer reveal
            answer_spans = check_soup.find_all("span", class_="answer-button")
            for asp in answer_spans[:2]:
                print(f"Answer button: {asp.get_text(strip=True)[:100]}")

            # Look for the actual answer text
            for div in check_soup.find_all("div", class_=lambda c: c and "answer" in str(c).lower()):
                print(f"Answer div: class={div.get('class')} text={div.get_text(strip=True)[:200]}")

asyncio.run(research())
