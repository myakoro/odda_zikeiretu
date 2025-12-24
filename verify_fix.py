import sqlite3
import os

DB_PATH = 'data/odds_history.db'

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print("--- Database Tables ---")
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for row in cur.fetchall():
        print(f"Table: {row[0]}")
    
    print("\n--- Races Count ---")
    try:
        cur.execute("SELECT COUNT(*) FROM races")
        print(f"Races: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"Error checking races: {e}")

    print("\n--- Odds Sample (Recent Jan) ---")
    try:
        cur.execute("SELECT race_id, time_stamp, umaban, odds_fuku_min, odds_fuku_max FROM odds_history WHERE race_id LIKE '202501%' AND odds_fuku_min > 500 LIMIT 5")
        rows = cur.fetchall()
        if rows:
            print("Found strange large values:")
            for r in rows:
                print(f"  {r[0]} {r[1]} 馬{r[2]}: {r[3]} - {r[4]}")
        else:
            print("No strange large values (>500) found in Jan data.")
    except Exception as e:
        print(f"Error checking odds: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_db()
