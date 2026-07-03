"""Test the theme tree endpoint."""
import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as c:
        r = await c.post("http://localhost:8000/api/v1/auth/login", json={"email": "tutor@demo.com", "password": "demo123"})
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        r2 = await c.get("http://localhost:8000/api/v1/themes/subjects", headers=headers)
        subjects = r2.json()
        print(f"Subjects: {len(subjects)}")

        if subjects:
            subject_id = subjects[0]["id"]
            r3 = await c.get(f"http://localhost:8000/api/v1/themes/tree?subject_id={subject_id}", headers=headers)
            tree = r3.json()
            themes = tree.get("themes", [])
            print(f"Themes in tree: {len(themes)}")
            for t in themes[:5]:
                children = t.get("children", [])
                print(f"  {t.get('name')} ({t.get('fipi_code')}) - {len(children)} children")

            r4 = await c.get(f"http://localhost:8000/api/v1/themes/task-counts?subject_id={subject_id}", headers=headers)
            counts = r4.json()
            print(f"\nTask counts: {len(counts)} themes")
            for c_item in counts[:5]:
                print(f"  {c_item.get('name')}: {c_item.get('test_count')} TEST, {c_item.get('essay_count')} ESSAY")

asyncio.run(test())
