import httpx

r = httpx.post("http://localhost:8000/api/v1/auth/login", json={"email": "tutor@demo.com", "password": "demo123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

r2 = httpx.get("http://localhost:8000/api/v1/themes/subjects", headers=h)
subjects = r2.json()

for subj in subjects:
    r3 = httpx.get(f"http://localhost:8000/api/v1/themes/tree?subject_id={subj['id']}", headers=h)
    tree = r3.json()
    themes = tree.get("themes", [])
    print(f"\nSubject: {subj['name']} ({subj['id']})")
    print(f"  Root themes: {len(themes)}")
    for t in themes[:5]:
        children = t.get("children", [])
        print(f"    {t['fipi_code']}: {t['name']} ({len(children)} children)")
        for c in children[:2]:
            print(f"      {c['fipi_code']}: {c['name']}")
