"""Research: try correct answer format."""
import asyncio
import httpx
from bs4 import BeautifulSoup

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
            selects = form.find_all("select")
            print(f"GUID: {guid}, Selects: {len(selects)}")

            # Try different answer formats
            for answer in ["0123", "1234", "0000", "1111", "2222", "3333", "4444", "5555", "6666"]:
                check_data = {
                    "guid": guid,
                    "answer": answer,
                    "ajax": "1",
                    "proj": "068A227D253BA6C04D0C832387FD0D89",
                }
                check_resp = await client.post(f"{BASE}/solve.php", data=check_data, headers=HEADERS)
                result = check_resp.text.strip()
                print(f"  Answer '{answer}': result='{result}'")

            # Also check a SHORT_ANSWER task
            print("\n=== SHORT_ANSWER task ===")
            # Fetch more tasks to find a short answer one
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

            # Find a short answer task
            for qb in soup2.find_all("div", class_="qblock"):
                form2 = qb.find("form", id=lambda x: x and x.startswith("checkform"))
                if form2:
                    selects2 = form2.find_all("select")
                    text_inputs = form2.find_all("input", type="text")
                    if not selects2 and text_inputs:
                        guid2 = form2.find("input", {"name": "guid"}).get("value", "")
                        print(f"Short answer task GUID: {guid2}")
                        print(f"Text inputs: {len(text_inputs)}")
                        for ti in text_inputs:
                            print(f"  input name={ti.get('name')} value={ti.get('value', '')}")

                        # Try to check with text answer
                        for ans in ["москва", "петр", "1917", "росси"]:
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
