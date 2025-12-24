import sys
import os

# srcをインポートパスに追加
sys.path.append(os.path.join(os.getcwd(), 'src'))

from parser import JVDataParser
import shutil

def test_parser_fix():
    # テスト用のDBを作成
    test_db = 'data/test_verify.db'
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # テーブル作成
    import sqlite3
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE odds_history (
            race_id TEXT,
            time_stamp TEXT,
            umaban INTEGER,
            odds_tan REAL,
            odds_fuku_min REAL,
            odds_fuku_max REAL,
            popularity INTEGER,
            PRIMARY KEY (race_id, time_stamp, umaban)
        )
    ''')
    conn.commit()
    conn.close()

    parser = JVDataParser(test_db)
    
    # ダミーのO1レコードを作成
    # ヘッダー (0-43)
    data = bytearray(b'O1' + b' ' * 41)
    # レースキー (11-27)
    race_id_bytes = b'202501130602'
    data[11:11+12] = race_id_bytes
    # 発表時刻 (27-35)
    data[27:35] = b'01130916'
    
    # 単勝部 (43-267) - 28頭分 (1頭8バイト: 馬番2, 単勝4, 人気2)
    for i in range(1, 19):
        offset = 43 + (i-1)*8
        data[offset:offset+2] = f"{i:02d}".encode('ascii')
        data[offset+2:offset+6] = b'0138' # 13.8
        data[offset+6:offset+8] = b'01'
    
    # 馬19-28をゼロ埋め (umaban=0でストップさせるため)
    for i in range(19, 29):
        offset = 43 + (i-1)*8
        data[offset:offset+8] = b'00' + b' ' * 6
    
    # 複勝部 (267-547) - 28頭分 (1頭10バイト: 馬番2, 下限4, 上限4)
    # 正常なデータ
    for i in range(1, 19):
        offset = 267 + (i-1)*10
        data[offset:offset+2] = f"{i:02d}".encode('ascii')
        data[offset+2:offset+6] = b'0051' # 5.1
        data[offset+6:offset+10] = b'0088' # 8.8

    print("--- Testing normal O1 record ---")
    print(f"  Data length: {len(data)}")
    print(f"  RA Key: {data[11:27].decode('ascii')}")
    print(f"  Ann Time: {data[27:35].decode('ascii')}")
    
    parser.parse_odds_record(data, "O1")
    parser.commit()
    
    # 検証
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("SELECT race_id, time_stamp, umaban, odds_tan, odds_fuku_min, odds_fuku_max FROM odds_history WHERE umaban=1")
    res = cur.fetchone()
    if res:
        print(f"馬1: 単勝{res[3]} 複勝{res[4]}-{res[5]}")
        if res[4] == 5.1 and res[5] == 8.8:
            print(">> NORMAL DATA: OK")
        else:
            print(">> NORMAL DATA: FAILED")
    
    # 異常データ（下限 > 上限）のシミュレーション
    print("\n--- Testing anomaly (min > max) handle ---")
    data_bad = data.copy()
    offset1 = 267 # 馬1
    data_bad[offset1+2:offset1+6] = b'9714'
    data_bad[offset1+6:offset1+10] = b'0400'
    
    parser.parse_odds_record(data_bad, "O1") # これはスキップされるはず
    parser.commit()
    
    cur.execute("SELECT odds_fuku_min, odds_fuku_max FROM odds_history WHERE umaban=1")
    res = cur.fetchone()
    print(f"馬1の値: {res[0]} - {res[1]} (変更されていないはず)")
    if res[0] == 5.1:
        print(">> ANOMALY SKIP: OK")
    else:
        print(">> ANOMALY SKIP: FAILED (Value updated to bad data)")

    parser.close()
    if os.path.exists(test_db):
        os.remove(test_db)

if __name__ == "__main__":
    test_parser_fix()
