"""Fix theme-subject associations."""
import psycopg2

conn = psycopg2.connect(host='localhost', port=5432, user='repetitor', password='repetitor', dbname='repetitor')
cur = conn.cursor()

# Get subject IDs
cur.execute("SELECT id, name FROM subjects")
subjects = {r[1]: r[0] for r in cur.fetchall()}
print("Subjects:", subjects)

# Themes that should be in Обществознание (not История)
social_codes = ['10.', '10.1.', '10.2.', '11.', '11.1.', '11.2.', '12.', '12.1.', '12.2.']
social_subject = subjects.get('Обществознание')
history_subject = subjects.get('История')

if not social_subject:
    print("Обществознание subject not found!")
    conn.close()
    exit()

# Move social themes to Обществознание subject
moved = 0
for code in social_codes:
    cur.execute("SELECT id, name, subject_id FROM themes WHERE fipi_code = %s", (code,))
    theme = cur.fetchone()
    if theme and theme[2] == history_subject:
        cur.execute("UPDATE themes SET subject_id = %s WHERE id = %s", (social_subject, theme[0]))
        moved += 1
        print(f"  Moved: {code} ({theme[1]}) -> Обществознание")

conn.commit()
print(f"\nMoved {moved} themes")

# Also fix child themes of moved parents
cur.execute("""
    WITH RECURSIVE children AS (
        SELECT id, parent_theme_id FROM themes WHERE fipi_code IN ('10.', '10.1.', '10.2.', '11.', '11.1.', '11.2.', '12.', '12.1.', '12.2.')
        UNION ALL
        SELECT t.id, t.parent_theme_id FROM themes t JOIN children c ON t.parent_theme_id = c.id
    )
    UPDATE themes SET subject_id = %s WHERE id IN (SELECT id FROM children) AND subject_id = %s
""", (social_subject, history_subject))
print(f"Updated child themes: {cur.rowcount}")

conn.commit()

# Verify
cur.execute("""
    SELECT t.fipi_code, t.name, s.name as subject
    FROM themes t JOIN subjects s ON t.subject_id = s.id
    WHERE t.fipi_code LIKE '1%' OR t.fipi_code LIKE '10%' OR t.fipi_code LIKE '11%' OR t.fipi_code LIKE '12%'
    ORDER BY t.fipi_code
""")
print("\nVerification:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]} [{r[2]}]")

conn.close()
