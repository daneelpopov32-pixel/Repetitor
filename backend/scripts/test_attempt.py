import httpx

# Login as student
r = httpx.post("http://localhost:8000/api/v1/auth/login", json={"email": "student@demo.com", "password": "demo123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# Get tutor's test
r_tutor = httpx.post("http://localhost:8000/api/v1/auth/login", json={"email": "tutor@demo.com", "password": "demo123"})
tutor_token = r_tutor.json()["access_token"]
r2 = httpx.get("http://localhost:8000/api/v1/tests", headers={"Authorization": f"Bearer {tutor_token}"})
tests = r2.json()
if tests:
    test_id = tests[0]["test_id"]
    print(f"Test: {tests[0]['title']} ({test_id})")

    # Assign test to student
    r3 = httpx.post(
        f"http://localhost:8000/api/v1/tests/{test_id}/assign",
        json={"student_ids": [r.json()["user_id"]]},
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    print(f"Assign: {r3.status_code}")

    # Start attempt
    r4 = httpx.post(
        f"http://localhost:8000/api/v1/attempts/0/start?test_id={test_id}",
        headers=h,
    )
    print(f"Start attempt: {r4.status_code} {r4.json()}")
else:
    print("No tests found")
