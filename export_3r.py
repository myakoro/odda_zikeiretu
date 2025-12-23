"""
中京3Rのデータを出力
"""
import sqlite3
import csv

# データベース接続
conn = sqlite3.connect('data/odds_history.db')
c = conn.cursor()

# 中京3R (202512060703) のデータを抽出
race_id = '202512060703'

print(f"レースID {race_id} のデータをエクスポートしています...")

# レース情報を取得
c.execute('SELECT * FROM races WHERE race_id = ?', (race_id,))
race_info = c.fetchone()

if race_info:
    print(f"\nレース情報:")
    print(f"  レースID: {race_info[0]}")
    print(f"  日付: {race_info[1]}")
    print(f"  競馬場コード: {race_info[2]}")
    print(f"  レース番号: {race_info[3]}")
    print(f"  レース名: {race_info[4]}")
    print(f"  発走時刻: {race_info[5]}")
else:
    print(f"\n[ERROR] レースID {race_id} が見つかりません")
    conn.close()
    exit(1)

# オッズデータを取得
c.execute('''
    SELECT time_stamp, umaban, odds_tan, odds_fuku_min, odds_fuku_max
    FROM odds_history 
    WHERE race_id = ?
    ORDER BY time_stamp, umaban
''', (race_id,))

odds_data = c.fetchall()

print(f"\n総レコード数: {len(odds_data):,} 件")

if len(odds_data) == 0:
    print(f"\n[WARNING] オッズデータがありません")
    conn.close()
    exit(0)

# CSVファイルに出力
output_file = 'target系/インポート確認_中京3R.csv'

with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    
    # ヘッダー
    writer.writerow(['時刻', '馬番', '単勝オッズ', '複勝オッズ下限', '複勝オッズ上限'])
    
    # データ
    for row in odds_data:
        writer.writerow(row)

print(f"\n✓ エクスポート完了: {output_file}")
print(f"  {len(odds_data):,} 件のレコードを出力しました")

# 時系列データのサマリー
c.execute('''
    SELECT 
        MIN(time_stamp) as first_time,
        MAX(time_stamp) as last_time,
        COUNT(DISTINCT time_stamp) as time_points,
        COUNT(DISTINCT umaban) as horses
    FROM odds_history 
    WHERE race_id = ?
''', (race_id,))

summary = c.fetchone()
print(f"\nデータサマリー:")
print(f"  最初の時刻: {summary[0]}")
print(f"  最後の時刻: {summary[1]}")
print(f"  時刻ポイント数: {summary[2]} 個")
print(f"  馬番数: {summary[3]} 頭")

# オッズが入っている時刻を確認
c.execute('''
    SELECT DISTINCT time_stamp
    FROM odds_history 
    WHERE race_id = ? AND odds_tan > 0
    ORDER BY time_stamp
    LIMIT 3
''', (race_id,))

valid_times = [row[0] for row in c.fetchall()]

if valid_times:
    print(f"\nオッズが入っている時刻（最初の3つ）:")
    for t in valid_times:
        print(f"  - {t}")
    
    # 最初のオッズが入っている時刻のデータを表示
    first_valid_time = valid_times[0]
    print(f"\n{first_valid_time} のオッズデータ（馬番1-10）:")
    print("=" * 60)
    
    c.execute('''
        SELECT umaban, odds_tan, odds_fuku_min, odds_fuku_max
        FROM odds_history 
        WHERE race_id = ? AND time_stamp = ? AND umaban <= 10
        ORDER BY umaban
    ''', (race_id, first_valid_time))
    
    print(f"{'馬番':>4} {'単勝オッズ':>10} {'複勝下限':>10} {'複勝上限':>10}")
    print("-" * 60)
    
    for row in c.fetchall():
        print(f"{row[0]:>4} {row[1]:>10.1f} {row[2]:>10.1f} {row[3]:>10.1f}")

conn.close()
