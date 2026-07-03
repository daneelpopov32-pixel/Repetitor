import httpx, time

r = httpx.post("http://localhost:8000/api/v1/auth/login", json={"email": "tutor@demo.com", "password": "demo123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# Test theme tree
r2 = httpx.get("http://localhost:8000/api/v1/themes/subjects", headers=h)
subj = r2.json()[0]
r3 = httpx.get(f"http://localhost:8000/api/v1/themes/tree?subject_id={subj['id']}", headers=h)
tree = r3.json()
print(f"Themes: {len(tree['themes'])}")
for t in tree['themes'][:5]:
    print(f"  {t['fipi_code']}: {t['name']} ({len(t.get('children', []))} children)")

# Test create with theme "1."
print("\n--- Creating test with theme '1.' ---")
r4 = httpx.post(
    "http://localhost:8000/api/v1/fipi/create-test",
    json={"title": "Test Fix", "theme_codes": ["1."], "count_per_theme": 3, "task_type": "TEST"},
    headers=h,
)
print(f"Response: {r4.status_code} {r4.json()}")
task_id = r4.json()["task_id"]

for i in range(10):
    time.sleep(2)
    r5 = httpx.get(f"http://localhost:8000/api/v1/fipi/task-status/{task_id}", headers=h)
    status = r5.json()
    print(f"Poll {i+1}: {status['status']}")
    if status["status"] in ("SUCCESS", "FAILURE"):
        print("Result:", status.get("result", status.get("error")))
        break
