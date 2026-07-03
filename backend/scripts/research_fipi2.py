"""Research: fetch the questions iframe content."""
import asyncio
import httpx
from bs4 import BeautifulSoup
import json

BASE = "https://ege.fipi.ru/bank"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://ege.fipi.ru/bank/index.php?proj=068A227D253BA6C04D0C832387FD0D89",
}

async def research():
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, verify=False) as client:
        # Fetch the questions iframe
        url = f"{BASE}/questions.php?proj=068A227D253BA6C04D0C832387FD0D89&init_filter_themes=1"
        resp = await client.get(url, headers=HEADERS)
        print(f"Status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('content-type', 'unknown')}")
        text = resp.text
        print(f"Length: {len(text)}")

        soup = BeautifulSoup(text, "html.parser")

        print("\n=== INLINE SCRIPTS (search for theme/task data) ===")
        for script in soup.find_all("script", src=False):
            content = script.get_text(strip=True)
            if "theme" in content.lower() or "question" in content.lower() or "task" in content.lower() or "json" in content.lower() or "data" in content.lower():
                print(f"--- script (first 1000 chars) ---")
                print(content[:1000])

        print("\n=== ALL INLINE SCRIPTS (first 300 chars each) ===")
        for i, script in enumerate(soup.find_all("script", src=False)):
            content = script.get_text(strip=True)[:300]
            if content:
                print(f"[{i}] {content}")

        print("\n=== Forms ===")
        for form in soup.find_all("form"):
            print(f"  action={form.get('action')} method={form.get('method')} id={form.get('id')}")
            for inp in form.find_all("input"):
                print(f"    input name={inp.get('name')} type={inp.get('type')} value={inp.get('value', '')[:50]}")
            for sel in form.find_all("select"):
                print(f"    select name={sel.get('name')}")
                for opt in sel.find_all("option")[:5]:
                    print(f"      option value={opt.get('value')} text={opt.get_text(strip=True)[:50]}")

        print("\n=== divs with class containing 'question' or 'task' ===")
        for el in soup.find_all(["div", "section"], class_=lambda c: c and any(k in str(c).lower() for k in ["question", "task", "variant", "answer"])):
            text = el.get_text(strip=True)[:200]
            print(f"  tag={el.name} class={el.get('class')} text={text[:100]}")

        print("\n=== Raw HTML first 5000 chars ===")
        print(text[:5000])

asyncio.run(research())
