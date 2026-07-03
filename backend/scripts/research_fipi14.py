"""Research: check if there's an answer reveal endpoint."""
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
        # Fetch the questions page
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
            guid = form.find("input", {"name": "guid"}).get("value", "")
            print(f"GUID: {guid}")

            # Try solve.php with different parameters
            print("\n=== Testing solve.php with different params ===")
            for params in [
                {"guid": guid, "answer": "0123", "ajax": "1", "proj": "068A227D253BA6C04D0C832387FD0D89"},
                {"guid": guid, "answer": "0123", "ajax": "1", "proj": "068A227D253BA6C04D0C832387FD0D89", "show": "1"},
                {"guid": guid, "answer": "0123", "ajax": "1", "proj": "068A227D253BA6C04D0C832387FD0D89", "reveal": "1"},
                {"guid": guid, "answer": "0123", "ajax": "1", "proj": "068A227D253BA6C04D0C832387FD0D89", "check": "1"},
            ]:
                check_resp = await client.post(f"{BASE}/solve.php", data=params, headers=HEADERS)
                print(f"  Params {list(params.keys())}: status={check_resp.status_code}, content='{check_resp.text[:100]}'")

            # Try brute-force the answer for this matching task
            print("\n=== Brute-force answer ===")
            # The task has 4 selects with values 0-6
            # Try all combinations of 4 digits from 0-6
            correct_answer = None
            for a in range(7):
                for b in range(7):
                    for c in range(7):
                        for d in range(7):
                            answer = f"{a}{b}{c}{d}"
                            check_data = {
                                "guid": guid,
                                "answer": answer,
                                "ajax": "1",
                                "proj": "068A227D253BA6C04D0C832387FD0D89",
                            }
                            check_resp = await client.post(f"{BASE}/solve.php", data=check_data, headers=HEADERS)
                            result = check_resp.text.strip()
                            if result == "1":
                                correct_answer = answer
                                print(f"  FOUND CORRECT ANSWER: {answer}")
                                break
                        if correct_answer:
                            break
                    if correct_answer:
                        break
                if correct_answer:
                    break

            if not correct_answer:
                print("  Could not find correct answer (tried all 2401 combinations)")

            # Also try a SHORT_ANSWER task
            print("\n=== SHORT_ANSWER brute-force ===")
            data2 = {
                "search": "1",
                "pagesize": "50",
                "proj": "068A227D253BA6C04D0C832387FD0D89",
                "theme": "3.",
                "page": "1",
            }
            resp2 = await client.post(url, data=data2, headers=HEADERS)
            html2 = resp2.content.decode("windows-1251", errors="replace")
            soup2 = BeautifulSoup(html2, "html.parser")

            for qb in soup2.find_all("div", class_="qblock"):
                form2 = qb.find("form", id=lambda x: x and x.startswith("checkform"))
                if form2:
                    selects2 = form2.find_all("select")
                    text_inputs = form2.find_all("input", type="text")
                    if not selects2 and text_inputs:
                        guid2 = form2.find("input", {"name": "guid"}).get("value", "")
                        print(f"Short answer GUID: {guid2}")

                        # Get the task text to guess the answer
                        cell = qb.find("td", class_="cell_0")
                        if cell:
                            text = cell.get_text(strip=True)[:200]
                            print(f"  Task text: {text}")

                        # Try common answers
                        for ans in ["петр", "петра", "1703", "1721", "указ", " reform"]:
                            check_data = {
                                "guid": guid2,
                                "answer": ans,
                                "ajax": "1",
                                "proj": "068A227D253BA6C04D0C832387FD0D89",
                            }
                            check_resp = await client.post(f"{BASE}/solve.php", data=check_data, headers=HEADERS)
                            result = check_resp.text.strip()
                            print(f"  Answer '{ans}': result='{result}'")
                        break

asyncio.run(research())
