import httpx
import time

r = httpx.post("http://localhost:8000/api/v1/auth/login", json={"email": "tutor@demo.com", "password": "demo123"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

r2 = httpx.post(
    "http://localhost:8000/api/v1/fipi/create-test",
    json={"title": "Test 3", "theme_codes": ["1.", "2."], "count_per_theme": 3, "task_type": "TEST"},
    headers=headers,
)
print("Create response:", r2.status_code, r2.json())

task_id = r2.json()["task_id"]

for i in range(10):
    time.sleep(2)
    r3 = httpx.get(f"http://localhost:8000/api/v1/fipi/task-status/{task_id}", headers=headers)
    status = r3.json()
    print(f"Poll {i+1}: status={status['status']}")
    if status["status"] in ("SUCCESS", "FAILURE"):
        print("Result:", status.get("result", status.get("error")))
        break
