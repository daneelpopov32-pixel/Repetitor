"""Aggressively clean up duplicate themes."""
import psycopg2

conn = psycopg2.connect(host='localhost', port=5432, user='repetitor', password='repetitor', dbname='repetitor')
cur = conn.cursor()

# Find all themes with same name and subject_id
cur.execute("""
    SELECT t1.id, t1.fipi_code, t1.name, t1.subject_id
    FROM themes t1
    WHERE EXISTS (
        SELECT 1 FROM themes t2
        WHERE t2.name = t1.name AND t2.subject_id = t1.subject_id AND t2.id != t1.id
    )
    ORDER BY t1.name, t1.fipi_code
""")
all_themes = cur.fetchall()
print(f"Total themes: {len(all_themes)}")

# Group by name
from collections import defaultdict
groups = defaultdict(list)
for tid, code, name, sid in all_themes:
    groups[(name, sid)].append((tid, code))

# For each group, keep only the one with trailing dot
deleted = 0
for (name, sid), items in groups.items():
    if len(items) <= 1:
        continue

    # Sort: prefer trailing dot
    items.sort(key=lambda x: (not x[1].endswith('.'), x[1]))

    keep = items[0]
    for tid, code in items[1:]:
        # Move tasks to kept version
        cur.execute("UPDATE tasks SET theme_id = %s WHERE theme_id = %s", (keep[0], tid))
        cur.execute("UPDATE themes SET parent_theme_id = %s WHERE parent_theme_id = %s", (keep[0], tid))
        cur.execute("DELETE FROM themes WHERE id = %s", (tid,))
        deleted += 1
        print(f"  Deleted: {code} ({name})")

conn.commit()
print(f"\nDeleted {deleted} duplicate themes")

# Verify
cur.execute("SELECT fipi_code, name FROM themes ORDER BY fipi_code")
print(f"\nAll themes ({cur.rowcount}):")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()
