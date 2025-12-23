# データベースマイグレーションスクリプト v0.82

import sqlite3
import os

DB_PATH = 'data/odds_history.db'

def migrate_v082():
    """
    v0.8 → v0.82 へのマイグレーション
    odds_historyテーブルにUNIQUE制約を追加
    """
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        print("Please run init_db.py first.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 既存のUNIQUE制約を確認
        cursor.execute("PRAGMA table_info(odds_history)")
        print("Current odds_history schema:")
        for row in cursor.fetchall():
            print(f"  {row}")
        
        # UNIQUE制約を追加するには、テーブルを再作成する必要がある
        print("\nAdding UNIQUE constraint to odds_history...")
        
        # 1. 一時テーブルを作成
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS odds_history_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            race_id TEXT,
            time_stamp TEXT,
            umaban INTEGER,
            odds_tan REAL,
            odds_fuku_min REAL,
            odds_fuku_max REAL,
            popularity INTEGER,
            FOREIGN KEY (race_id) REFERENCES races(race_id),
            UNIQUE(race_id, time_stamp, umaban)
        )
        ''')
        
        # 2. データをコピー(重複を除去)
        cursor.execute('''
        INSERT OR IGNORE INTO odds_history_new 
        (id, race_id, time_stamp, umaban, odds_tan, odds_fuku_min, odds_fuku_max, popularity)
        SELECT id, race_id, time_stamp, umaban, odds_tan, odds_fuku_min, odds_fuku_max, popularity
        FROM odds_history
        ''')
        
        # 3. 古いテーブルを削除
        cursor.execute('DROP TABLE odds_history')
        
        # 4. 新しいテーブルをリネーム
        cursor.execute('ALTER TABLE odds_history_new RENAME TO odds_history')
        
        # 5. インデックスを再作成
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_odds_race_time ON odds_history (race_id, time_stamp)')
        
        conn.commit()
        print("Migration completed successfully!")
        
        # 結果を確認
        cursor.execute("PRAGMA table_info(odds_history)")
        print("\nNew odds_history schema:")
        for row in cursor.fetchall():
            print(f"  {row}")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_v082()
