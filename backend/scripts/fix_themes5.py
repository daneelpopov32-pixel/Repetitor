"""Remove themes without trailing dot (seed script leftovers)."""
import psycopg2

conn = psycopg2.connect(host='localhost', port=5432, user='repetitor', password='repetitor', dbname='repetitor')
cur = conn.cursor()

# Find themes without trailing dot that have a counterpart with trailing dot in same subject
cur.execute("""
    SELECT t1.id, t1.fipi_code, t1.name, t1.subject_id
    FROM themes t1
    WHERE t1.fipi_code !~ '\\.$' AND t1.fipi_code !~ '\\.\\d+\\.$'
""")
no_dot = cur.fetchall()
print(f"Themes without trailing dot: {len(no_dot)}")

for tid, code, name, sid in no_dot:
    # Check if there's a version with trailing dot in same subject
    cur.execute(
        "SELECT id FROM themes WHERE fipi_code = %s || '.' AND subject_id = %s",
        (code, sid)
    )
    match = cur.fetchone()
    if match:
        keep_id = match[0]
        cur.execute("UPDATE tasks SET theme_id = %s WHERE theme_id = %s", (keep_id, tid))
        cur.execute("UPDATE themes SET parent_theme_id = %s WHERE parent_theme_id = %s", (keep_id, tid))
        cur.execute("DELETE FROM themes WHERE id = %s", (tid,))
        print(f"  Merged: {code} -> {code}. ({name})")
    else:
        # No counterpart - fix the code by adding trailing dot
        cur.execute("UPDATE themes SET fipi_code = fipi_code || '.' WHERE id = %s", (tid,))
        print(f"  Fixed: {code} -> {code}. ({name})")

conn.commit()

# Final verification
cur.execute("SELECT fipi_code, name FROM themes ORDER BY fipi_code")
print(f"\nFinal themes ({cur.rowcount}):")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()
