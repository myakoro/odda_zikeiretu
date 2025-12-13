import sqlite3

def verify():
    try:
        conn = sqlite3.connect('data/odds_history.db')
        cursor = conn.cursor()
        
        print("--- RACES (Limit 10) ---")
        rows = cursor.execute("SELECT race_id, date, ba_code, race_no, race_name, start_time FROM races ORDER BY date DESC, race_id DESC LIMIT 10").fetchall()
        for r in rows:
            print(r)
        
        print("\n--- ODDS (Limit 10) ---")
        rows = cursor.execute("SELECT * FROM odds_history ORDER BY race_id DESC, umaban ASC LIMIT 10").fetchall()
        for r in rows:
            print(r)
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify()
