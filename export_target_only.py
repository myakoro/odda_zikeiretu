"""
ターゲットCSVからインポートしたデータだけを出力
"""
import sqlite3
import csv

conn = sqlite3.connect('data/odds_history.db')
c = conn.cursor()

race_id = '202512060701'

print(f"レースID {race_id} のターゲットCSVインポートデータのみを抽出")
print("=" * 80)

# ターゲットCSVからインポートしたデータ（popularity = 0）のみ取得
c.execute('''
    SELECT time_stamp, umaban, odds_tan, odds_fuku_min, odds_fuku_max
    FROM odds_history 
    WHERE race_id = ? AND popularity = 0
    ORDER BY time_stamp, umaban
''', (race_id,))

target_data = c.fetchall()

print(f"\nターゲットCSVインポートデータ: {len(target_data):,} 件")

if len(target_data) > 0:
    # CSVファイルに出力
    output_file = 'target系/ターゲットインポート分のみ_中京1R.csv'
    
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['時刻', '馬番', '単勝オッズ', '複勝オッズ下限', '複勝オッズ上限'])
        for row in target_data:
            writer.writerow(row)
    
    print(f"✓ エクスポート完了: {output_file}")
    
    # サンプル表示
    print(f"\nサンプルデータ（最初の20件）:")
    print(f"{'時刻':<20} {'馬番':>4} {'単勝':>8} {'複勝Lo':>8} {'複勝Hi':>8}")
    print("-" * 60)
    for row in target_data[:20]:
        print(f"{row[0]:<20} {row[1]:>4} {row[2]:>8.1f} {row[3]:>8.1f} {row[4]:>8.1f}")
    
    # 時系列範囲
    c.execute('''
        SELECT MIN(time_stamp), MAX(time_stamp), COUNT(DISTINCT time_stamp)
        FROM odds_history
        WHERE race_id = ? AND popularity = 0
    ''', (race_id,))
    time_range = c.fetchone()
    print(f"\n時系列範囲:")
    print(f"  最初: {time_range[0]}")
    print(f"  最後: {time_range[1]}")
    print(f"  時刻ポイント数: {time_range[2]}")

conn.close()
