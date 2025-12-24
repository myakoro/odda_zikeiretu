import sqlite3
conn = sqlite3.connect('data/odds_history.db')
cur = conn.cursor()

print("--- All Jan 2025 Race IDs in odds_history ---")
cur.execute("SELECT DISTINCT race_id FROM odds_history WHERE race_id LIKE '202501%' ORDER BY race_id ASC")
rows = cur.fetchall()
for r in rows:
    cur.execute("SELECT COUNT(*) FROM odds_history WHERE race_id=?", (r[0],))
    count = cur.fetchone()[0]
    print(f"  {r[0]} ({count} records)")
print(f"Total Jan 2025 daily venues/races: {len(rows)}")

conn.close()
