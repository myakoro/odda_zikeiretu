"""
インポートしたデータの詳細確認（オッズが入っている時刻を表示）
"""
import sqlite3

# データベース接続
conn = sqlite3.connect('data/odds_history.db')
c = conn.cursor()

race_id = '202512060701'

print(f"レースID {race_id} の詳細確認\n")
print("=" * 80)

# オッズが0でない時刻を取得
c.execute('''
    SELECT DISTINCT time_stamp
    FROM odds_history 
    WHERE race_id = ? AND odds_tan > 0
    ORDER BY time_stamp
    LIMIT 5
''', (race_id,))

valid_times = [row[0] for row in c.fetchall()]

if valid_times:
    print(f"オッズが入っている時刻（最初の5つ）:")
    for t in valid_times:
        print(f"  - {t}")
    
    # 最初のオッズが入っている時刻のデータを表示
    first_valid_time = valid_times[0]
    print(f"\n{first_valid_time} のオッズデータ（全馬番）:")
    print("=" * 80)
    
    c.execute('''
        SELECT umaban, odds_tan, odds_fuku_min, odds_fuku_max
        FROM odds_history 
        WHERE race_id = ? AND time_stamp = ?
        ORDER BY umaban
    ''', (race_id, first_valid_time))
    
    print(f"{'馬番':>4} {'単勝オッズ':>10} {'複勝下限':>10} {'複勝上限':>10}")
    print("-" * 80)
    
    for row in c.fetchall():
        print(f"{row[0]:>4} {row[1]:>10.1f} {row[2]:>10.1f} {row[3]:>10.1f}")
    
    # 2番目の時刻も表示
    if len(valid_times) > 1:
        second_valid_time = valid_times[1]
        print(f"\n{second_valid_time} のオッズデータ（全馬番）:")
        print("=" * 80)
        
        c.execute('''
            SELECT umaban, odds_tan, odds_fuku_min, odds_fuku_max
            FROM odds_history 
            WHERE race_id = ? AND time_stamp = ?
            ORDER BY umaban
        ''', (race_id, second_valid_time))
        
        print(f"{'馬番':>4} {'単勝オッズ':>10} {'複勝下限':>10} {'複勝上限':>10}")
        print("-" * 80)
        
        for row in c.fetchall():
            print(f"{row[0]:>4} {row[1]:>10.1f} {row[2]:>10.1f} {row[3]:>10.1f}")

# 時系列推移を確認（馬番1のオッズ推移）
print(f"\n\n馬番1の単勝オッズ時系列推移（最初の20ポイント）:")
print("=" * 80)

c.execute('''
    SELECT time_stamp, odds_tan, odds_fuku_min, odds_fuku_max
    FROM odds_history 
    WHERE race_id = ? AND umaban = 1 AND odds_tan > 0
    ORDER BY time_stamp
    LIMIT 20
''', (race_id,))

print(f"{'時刻':<20} {'単勝':>10} {'複勝下限':>10} {'複勝上限':>10}")
print("-" * 80)

for row in c.fetchall():
    print(f"{row[0]:<20} {row[1]:>10.1f} {row[2]:>10.1f} {row[3]:>10.1f}")

conn.close()

print("\n" + "=" * 80)
print("✓ 確認完了")
print("  CSVファイル: target系/インポート確認_中京1R.csv")
print("=" * 80)
