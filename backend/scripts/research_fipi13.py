"""Research: look for hidden answer data in HTML."""
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

        # Get the first qblock
        qb = soup.find("div", class_="qblock")
        if qb:
            qid = qb.get("id", "")
            print(f"QBlock ID: {qid}")

            # Get the full HTML of this qblock
            qb_html = str(qb)

            # Search for hidden inputs, data attributes, comments
            print("\n=== Hidden inputs ===")
            for inp in qb.find_all("input", type="hidden"):
                print(f"  name={inp.get('name')} value={inp.get('value', '')[:50]}")

            print("\n=== Data attributes ===")
            for el in qb.find_all(True):
                for attr in el.attrs:
                    if attr.startswith("data-"):
                        print(f"  {el.name} {attr}={el.attrs[attr]}")

            print("\n=== HTML comments ===")
            for comment in qb.find_all(string=lambda text: isinstance(text, type(qb.new_string(""))) and text.strip().startswith("<!--")):
                print(f"  {comment[:200]}")

            # Search for answer patterns in the HTML
            print("\n=== Answer patterns in HTML ===")
            # Look for patterns like "answer", "correct", "right"
            for pattern in [r'answer["\s:=]+["\']?(\w+)', r'correct["\s:=]+["\']?(\w+)', r'right["\s:=]+["\']?(\w+)']:
                matches = re.findall(pattern, qb_html, re.IGNORECASE)
                if matches:
                    print(f"  Pattern '{pattern}': {matches[:5]}")

            # Look for the chkcode hidden input
            print("\n=== chkcode ===")
            chkcode_inputs = qb.find_all("input", {"name": "chkcode"})
            for ci in chkcode_inputs:
                print(f"  value='{ci.get('value', '')}'")

            # Check if there's a verify form
            print("\n=== Verify forms ===")
            for form in qb.find_all("form"):
                print(f"  form id={form.get('id')} action={form.get('action')}")

            # Look at the answer panel more carefully
            print("\n=== Answer panel details ===")
            answer_panel = qb.find("div", class_="answer-panel")
            if answer_panel:
                print(f"  Full HTML: {str(answer_panel)[:500]}")

            # Check for task-status div
            print("\n=== task-status ===")
            task_status = qb.find("div", class_="task-status")
            if task_status:
                print(f"  HTML: {str(task_status)[:300]}")

            # Print the full qblock HTML (first 3000 chars)
            print("\n=== Full qblock HTML (first 3000 chars) ===")
            print(qb_html[:3000])

asyncio.run(research())
