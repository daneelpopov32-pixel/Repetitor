import httpx

r = httpx.post("http://localhost:8000/api/v1/auth/login", json={"email": "tutor@demo.com", "password": "demo123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

r2 = httpx.get("http://localhost:8000/api/v1/themes/subjects", headers=h)
subjects = r2.json()
history_id = subjects[0]["id"]  # История

r3 = httpx.get(f"http://localhost:8000/api/v1/themes/tree?subject_id={history_id}", headers=h)
tree = r3.json()
themes = tree.get("themes", [])

print(f"История: {len(themes)} root themes")
for t in themes:
    children = t.get("children", [])
    total = 1 + len(children)
    for c in children:
        total += len(c.get("children", []))
    print(f"  {t['fipi_code']}: {t['name']} ({total} total)")
