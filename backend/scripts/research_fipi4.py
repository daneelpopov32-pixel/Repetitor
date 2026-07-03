"""Research: extract full task structure from qblock."""
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
        url = f"{BASE}/questions.php?proj=068A227D253BA6C04D0C832387FD0D89&init_filter_themes=1"
        resp = await client.get(url, headers=HEADERS)
        try:
            html = resp.content.decode("windows-1251")
        except:
            html = resp.text

        soup = BeautifulSoup(html, "html.parser")

        # Find all qblock divs
        qblocks = soup.find_all("div", class_="qblock")
        print(f"Found {len(qblocks)} qblocks\n")

        # Analyze first 3 qblocks in detail
        for i, qb in enumerate(qblocks[:3]):
            print(f"=== QBlock {i+1} ===")

            # Get the task header
            header = qb.find("div", class_="task-header-panel")
            if header:
                print(f"  Header HTML: {str(header)[:500]}")

            # Get the task info
            info = qb.find("div", class_="task-info-panel")
            if info:
                title_div = info.find("div", class_="task-info-title")
                content_div = info.find("div", class_="task-info-content")
                if title_div:
                    print(f"  Title: {title_div.get_text(strip=True)[:200]}")
                if content_div:
                    print(f"  Content: {content_div.get_text(strip=True)[:300]}")

            # Find the form
            form = qb.find("form", id=lambda x: x and x.startswith("checkform"))
            if form:
                form_id = form.get("id", "")
                print(f"  Form ID: {form_id}")

                # Check for selects (matching tasks)
                selects = form.find_all("select")
                if selects:
                    print(f"  Type: MATCHING (has {len(selects)} selects)")
                else:
                    # Check for other input types
                    inputs = form.find_all("input", type="text")
                    if inputs:
                        print(f"  Type: SHORT_ANSWER (has text inputs)")
                    else:
                        print(f"  Type: ESSAY or UNKNOWN")

            # Find the answer panel
            answer_panel = qb.find("div", class_="answer-panel")
            if answer_panel:
                print(f"  Answer panel: {answer_panel.get_text(strip=True)[:100]}")

            # Get the full HTML of the qblock (first 2000 chars)
            print(f"  Full HTML (first 1500 chars):")
            print(f"  {str(qb)[:1500]}")
            print()

        # Now try to filter by theme
        print("\n=== THEME FILTER TEST ===")
        # Try POST with theme filter
        filter_url = f"{BASE}/questions.php"
        filter_data = {
            "search": "1",
            "pagesize": "10",
            "proj": "068A227D253BA6C04D0C832387FD0D89",
            "theme": "1.",  # Try theme 1
            "page": "1",
        }
        resp2 = await client.post(filter_url, data=filter_data, headers=HEADERS)
        try:
            html2 = resp2.content.decode("windows-1251")
        except:
            html2 = resp2.text
        soup2 = BeautifulSoup(html2, "html.parser")
        qblocks2 = soup2.find_all("div", class_="qblock")
        print(f"Theme 1 filter: {len(qblocks2)} qblocks")
        for qb in qblocks2[:2]:
            header = qb.find("div", class_="task-header-panel")
            if header:
                print(f"  Header: {header.get_text(strip=True)[:200]}")

asyncio.run(research())
