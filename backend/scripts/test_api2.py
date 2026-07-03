"""Test the theme tree endpoint - debug."""
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
            print(f"Tree status: {r3.status_code}")
            print(f"Tree response: {r3.text[:500]}")

asyncio.run(test())
