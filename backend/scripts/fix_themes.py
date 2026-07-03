"""Clean up duplicate themes and fix fipi_codes."""
import psycopg2

conn = psycopg2.connect(host='localhost', port=5432, user='repetitor', password='repetitor', dbname='repetitor')
cur = conn.cursor()

# Find duplicate themes (same name, different fipi_code)
cur.execute("""
    SELECT t1.id, t1.fipi_code, t1.name, t2.id as dup_id, t2.fipi_code as dup_code
    FROM themes t1
    JOIN themes t2 ON t1.name = t2.name AND t1.id != t2.id
    WHERE t1.subject_id = t2.subject_id
""")
dups = cur.fetchall()
print(f"Found {len(dups)} duplicate theme pairs")

# Identify which to keep (the one with trailing dot = correct FIPI code)
to_delete = set()
for row in dups:
    keep_id, keep_code, name, dup_id, dup_code = row
    # Prefer the one with trailing dot
    if keep_code.endswith('.') and not dup_code.endswith('.'):
        to_delete.add(dup_id)
    elif dup_code.endswith('.') and not keep_code.endswith('.'):
        to_delete.add(keep_id)
    else:
        # Both have or don't have trailing dot - keep the one with more tasks
        cur.execute("SELECT COUNT(*) FROM tasks WHERE theme_id = %s", (keep_id,))
        keep_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tasks WHERE theme_id = %s", (dup_id,))
        dup_count = cur.fetchone()[0]
        if dup_count > keep_count:
            to_delete.add(keep_id)
        else:
            to_delete.add(dup_id)

print(f"Themes to delete: {len(to_delete)}")

# Also find themes with codes that don't end with dot (except leaf themes)
cur.execute("SELECT id, fipi_code, name FROM themes WHERE fipi_code ~ '^[0-9]+(\\.[0-9]+)*$' AND fipi_code NOT LIKE '%.'")
no_dot = cur.fetchall()
for tid, code, name in no_dot:
    if code not in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'):
        # These are sub-themes without trailing dot
        # Check if there's a version with trailing dot
        cur.execute("SELECT id FROM themes WHERE fipi_code = %s || '.' AND subject_id = (SELECT subject_id FROM themes WHERE id = %s)", (code, tid))
        match = cur.fetchone()
        if match:
            to_delete.add(tid)
            print(f"  Will delete: {code} ({name}) - duplicate of {code}.")
        else:
            # No duplicate - fix the code by adding trailing dot
            cur.execute("UPDATE themes SET fipi_code = fipi_code || '.' WHERE id = %s", (tid,))
            print(f"  Fixed: {code} -> {code}. ({name})")

# Delete duplicates
for tid in to_delete:
    # First move any tasks to the kept version
    cur.execute("SELECT fipi_code FROM themes WHERE id = %s", (tid,))
    code = cur.fetchone()[0]
    # Find the kept version
    cur.execute("SELECT id FROM themes WHERE fipi_code = %s || '.' AND subject_id = (SELECT subject_id FROM themes WHERE id = %s)", (code.rstrip('.'), tid))
    kept = cur.fetchone()
    if kept:
        kept_id = kept[0]
        cur.execute("UPDATE tasks SET theme_id = %s WHERE theme_id = %s", (kept_id, tid))
        cur.execute("UPDATE themes SET parent_theme_id = %s WHERE parent_theme_id = %s", (kept_id, tid))
        print(f"  Moved tasks from {code} to kept version")
    cur.execute("DELETE FROM themes WHERE id = %s", (tid,))
    print(f"  Deleted theme {code}")

conn.commit()

# Verify
cur.execute("SELECT fipi_code, name FROM themes WHERE fipi_code LIKE '1%' ORDER BY fipi_code")
print("\nRemaining themes starting with '1':")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()
