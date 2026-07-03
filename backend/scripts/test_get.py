import httpx

r = httpx.post("http://localhost:8000/api/v1/auth/login", json={"email": "tutor@demo.com", "password": "demo123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

r2 = httpx.get("http://localhost:8000/api/v1/tests", headers=h)
tests = r2.json()
print(f"Tests: {len(tests)}")

if tests:
    t = tests[0]
    r3 = httpx.get(f"http://localhost:8000/api/v1/tests/{t['test_id']}", headers=h)
    print(f"Detail status: {r3.status_code}")
    if r3.status_code == 200:
        detail = r3.json()
        print(f"Title: {detail['title']}")
        print(f"Tasks: {len(detail.get('tasks', []))}")
        for task in detail.get("tasks", [])[:3]:
            print(f"  {task['type']}: {str(task.get('text_content', {}))[:80]}")
