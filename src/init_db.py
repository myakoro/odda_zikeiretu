import sqlite3
import os

DB_PATH = 'data/odds_history.db'

def init_db():
    if os.path.exists(DB_PATH):
        print(f"Database already exists at {DB_PATH}")
        return

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # レース情報テーブル
    # JV-Link RA (レース詳細) 等から取得する基本情報
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS races (
        race_id TEXT PRIMARY KEY,
        date TEXT,
        ba_code TEXT, -- 場所コード
        race_no INTEGER,
        race_name TEXT,
        start_time TEXT
    )
    ''')

    # オッズ履歴テーブル
    # 時系列オッズを保存する。データ量が多くなるため適切にインデックスを貼る
    # race_id + time_stamp でユニークになる想定だが、
    # 同一時刻の更新もあり得るため、idを主キーとする。
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS odds_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        race_id TEXT,
        time_stamp TEXT, -- 取得時刻または発表時刻
        umaban INTEGER,
        odds_tan REAL, -- 単勝オッズ
        odds_fuku_min REAL, -- 複勝オッズ下限
        odds_fuku_max REAL, -- 複勝オッズ上限
        popularity INTEGER, -- 人気順
        FOREIGN KEY (race_id) REFERENCES races(race_id)
    )
    ''')
    
    # 馬連・馬単などのオッズテーブルも必要に応じて追加するが、まずは単複から。

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_odds_race_time ON odds_history (race_id, time_stamp)')

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == '__main__':
    init_db()
