"""
中京3Rのオッズが入っているデータだけを出力
"""
import sqlite3
import csv

conn = sqlite3.connect('data/odds_history.db')
c = conn.cursor()

race_id = '202512060703'

print(f"中京3R ({race_id}) のオッズ > 0 のデータのみを抽出")

# オッズが0でないデータのみ取得
c.execute('''
    SELECT time_stamp, umaban, odds_tan, odds_fuku_min, odds_fuku_max
    FROM odds_history 
    WHERE race_id = ? AND odds_tan > 0
    ORDER BY time_stamp, umaban
''', (race_id,))

data = c.fetchall()

print(f"総レコード数: {len(data):,} 件")

# CSVファイルに出力
output_file = 'target系/中京3R_オッズあり.csv'

with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['時刻', '馬番', '単勝オッズ', '複勝オッズ下限', '複勝オッズ上限'])
    for row in data:
        writer.writerow(row)

print(f"✓ エクスポート完了: {output_file}")

# サンプル表示（最初の時刻の全馬番）
first_time = data[0][0]
print(f"\n最初の時刻 ({first_time}) の全馬番:")
print(f"{'馬番':>4} {'単勝':>8} {'複勝Lo':>8} {'複勝Hi':>8}")
print("-" * 40)

for row in data:
    if row[0] == first_time:
        print(f"{row[1]:>4} {row[2]:>8.1f} {row[3]:>8.1f} {row[4]:>8.1f}")
    else:
        break

conn.close()
