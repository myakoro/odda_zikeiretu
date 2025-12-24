import sqlite3
conn = sqlite3.connect('data/odds_history.db')
cur = conn.cursor()

print("--- Data Counts ---")
cur.execute("SELECT substr(race_id, 1, 6) as month, COUNT(DISTINCT race_id) FROM odds_history GROUP BY month ORDER BY month DESC")
for r in cur.fetchall():
    print(f"  Month {r[0]}: {r[1]} races")

print("\n--- Recent Jan 26 Data ---")
cur.execute("SELECT DISTINCT race_id FROM odds_history WHERE race_id LIKE '20250126%' ORDER BY race_id ASC")
rows = cur.fetchall()
if rows:
    for r in rows:
        print(f"  Found Race ID: {r[0]}")
else:
    print("  No Jan 26 data found in odds_history.")

print("\n--- Latest 5 Race IDs ---")
cur.execute("SELECT DISTINCT race_id FROM odds_history ORDER BY race_id DESC LIMIT 5")
for r in cur.fetchall():
    print(f"  Race ID: {r[0]}")

conn.close()
