"""Research script: analyze FIPI page structure."""
import asyncio
import httpx
from bs4 import BeautifulSoup
import json

URL = "https://ege.fipi.ru/bank/index.php?proj=068A227D253BA6C04D0C832387FD0D89"

async def research():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, verify=False) as client:
        try:
            resp = await client.get(URL, headers=headers)
            print(f"Status: {resp.status_code}")
            print(f"Content-Type: {resp.headers.get('content-type', 'unknown')}")
            print(f"Content length: {len(resp.text)}")

            soup = BeautifulSoup(resp.text, "html.parser")

            print("\n=== TITLE ===")
            title = soup.find("title")
            print(title.get_text(strip=True) if title else "No title")

            print("\n=== SCRIPTS (src) ===")
            for script in soup.find_all("script", src=True)[:20]:
                print(f"  {script['src']}")

            print("\n=== INLINE SCRIPTS (first 500 chars each) ===")
            for script in soup.find_all("script", src=False)[:5]:
                text = script.get_text(strip=True)[:500]
                if text:
                    print(f"  --- script ---")
                    print(f"  {text}")

            print("\n=== FORMS ===")
            for form in soup.find_all("form"):
                print(f"  action={form.get('action')} method={form.get('method')}")

            print("\n=== IFrames ===")
            for iframe in soup.find_all("iframe"):
                print(f"  src={iframe.get('src')}")

            print("\n=== DIV/SECTION with class containing 'task' or 'question' ===")
            for el in soup.find_all(["div", "section"], class_=lambda c: c and any(k in str(c).lower() for k in ["task", "question", "задани"])):
                print(f"  tag={el.name} class={el.get('class')} id={el.get('id')}")

            print("\n=== All classes on body-level divs ===")
            for div in soup.find_all("div", recursive=False)[:30]:
                cls = div.get("class", [])
                did = div.get("id", "")
                print(f"  class={cls} id={did}")

            print("\n=== Raw HTML first 3000 chars ===")
            print(resp.text[:3000])

        except Exception as e:
            print(f"Error: {e}")

asyncio.run(research())
