"""Research: deep-dive into task structure."""
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
        # Try to decode as windows-1251
        try:
            html = resp.content.decode("windows-1251")
        except:
            html = resp.text

        soup = BeautifulSoup(html, "html.parser")

        # Find all task blocks - each task has a form with checkform{ID}
        task_forms = soup.find_all("form", id=lambda x: x and x.startswith("checkform"))
        print(f"Found {len(task_forms)} task forms\n")

        # Analyze first 3 tasks in detail
        for i, form in enumerate(task_forms[:3]):
            form_id = form.get("id", "")
            task_id = form_id.replace("checkform", "")
            print(f"=== Task {i+1} (ID: {task_id}) ===")

            # Find GUID
            guid_input = form.find("input", {"name": "guid"})
            if guid_input:
                print(f"  GUID: {guid_input.get('value')}")

            # Find answer inputs
            answer_input = form.find("input", {"name": "answer"})
            if answer_input:
                print(f"  Answer type: hidden")

            # Find select elements (matching tasks)
            selects = form.find_all("select")
            if selects:
                print(f"  Selects: {len(selects)}")
                for s in selects:
                    name = s.get("name", "")
                    options = s.find_all("option")
                    print(f"    {name}: {len(options)} options")
                    for o in options[:3]:
                        print(f"      value={o.get('value')} text={o.get_text(strip=True)[:60]}")

            # Find the parent task block
            task_block = form.find_parent("div", class_=lambda c: c and "task" in str(c).lower())
            if not task_block:
                # Try finding by sibling relationship
                task_block = form.parent

            # Look for the task content div
            # The task text is typically in a div after the form
            print(f"  Parent tag: {task_block.name if task_block else 'None'}")
            print(f"  Parent class: {task_block.get('class') if task_block else 'None'}")

            # Find task info panel
            info_panel = soup.find("div", class_="task-info-panel")
            if info_panel:
                title = info_panel.find("div", class_="task-info-title")
                content = info_panel.find("div", class_="task-info-content")
                if title:
                    print(f"  Theme: {title.get_text(strip=True)[:100]}")
                if content:
                    print(f"  Content: {content.get_text(strip=True)[:200]}")

            # Look for task number
            task_header = soup.find("div", class_="task-header-panel")
            if task_header:
                print(f"  Header: {task_header.get_text(strip=True)[:200]}")

            print()

        # Now let's look at the theme filter mechanism
        print("=== THEME FILTER ===")
        # Find the theme filter form
        filter_form = soup.find("form", id="filters")
        if filter_form:
            selects = filter_form.find_all("select")
            for s in selects:
                name = s.get("name", "")
                options = s.find_all("option")
                print(f"  Select '{name}': {len(options)} options")
                for o in options[:10]:
                    print(f"    value={o.get('value')} text={o.get_text(strip=True)[:60]}")

        # Look for the check answer mechanism
        print("\n=== ANSWER CHECK SCRIPTS ===")
        for script in soup.find_all("script", src=False):
            text = script.get_text(strip=True)
            if "checkAnswer" in text or "setAnswer" in text or "Verify" in text:
                print(text[:500])
                print("---")

        # Look for the theme list in JavaScript
        print("\n=== THEME LIST IN JS ===")
        for script in soup.find_all("script", src=False):
            text = script.get_text(strip=True)
            if "setAllThemes" in text or "allThemes" in text or "themes" in text.lower():
                # Find the setAllThemes call
                match = re.search(r'setAllThemes\("([^"]+)"\)', text)
                if match:
                    themes = match.group(1)
                    print(f"Themes: {themes[:500]}")

asyncio.run(research())
