"""Final cleanup: deduplicate within same subject."""
import psycopg2

conn = psycopg2.connect(host='localhost', port=5432, user='repetitor', password='repetitor', dbname='repetitor')
cur = conn.cursor()

# Find duplicates within same subject
cur.execute("""
    SELECT t1.id, t1.fipi_code, t1.name, t1.subject_id,
           t2.id as dup_id, t2.fipi_code as dup_code
    FROM themes t1
    JOIN themes t2 ON t1.name = t2.name AND t1.subject_id = t2.subject_id AND t1.id > t2.id
""")
dups = cur.fetchall()
print(f"Found {len(dups)} within-subject duplicates")

for row in dups:
    t1_id, t1_code, name, sid, t2_id, t2_code = row
    # Keep the one with trailing dot
    if t1_code.endswith('.'):
        keep_id, keep_code, del_id, del_code = t1_id, t1_code, t2_id, t2_code
    else:
        keep_id, keep_code, del_id, del_code = t2_id, t2_code, t1_id, t1_code

    cur.execute("UPDATE tasks SET theme_id = %s WHERE theme_id = %s", (keep_id, del_id))
    cur.execute("UPDATE themes SET parent_theme_id = %s WHERE parent_theme_id = %s", (keep_id, del_id))
    cur.execute("DELETE FROM themes WHERE id = %s", (del_id,))
    print(f"  Merged: {del_code} -> {keep_code} ({name})")

conn.commit()

# Final count
cur.execute("SELECT COUNT(*) FROM themes")
print(f"\nTotal themes: {cur.fetchone()[0]}")

cur.execute("SELECT fipi_code, name FROM themes WHERE fipi_code LIKE '1%' OR fipi_code LIKE '2%' ORDER BY fipi_code")
print("Themes 1-2:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()
