"""
データベースの内容を詳しく確認
"""
import sqlite3

conn = sqlite3.connect('data/odds_history.db')
c = conn.cursor()

print("=" * 80)
print("データベース全体の確認")
print("=" * 80)

# 全レース数
c.execute('SELECT COUNT(*) FROM races')
total_races = c.fetchone()[0]
print(f"\n総レース数: {total_races}")

# 全オッズレコード数
c.execute('SELECT COUNT(*) FROM odds_history')
total_odds = c.fetchone()[0]
print(f"総オッズレコード数: {total_odds:,}")

# 12月6日のレース一覧
print("\n" + "=" * 80)
print("12月6日のレース一覧")
print("=" * 80)
c.execute('''
    SELECT race_id, ba_code, race_no, race_name, 
           (SELECT COUNT(*) FROM odds_history WHERE odds_history.race_id = races.race_id) as odds_count
    FROM races 
    WHERE date = '2025-12-06'
    ORDER BY race_id
''')

print(f"{'レースID':<15} {'場':<4} {'R':<3} {'レース名':<30} {'オッズ数':>10}")
print("-" * 80)
for row in c.fetchall():
    print(f"{row[0]:<15} {row[1]:<4} {row[2]:<3} {row[3]:<30} {row[4]:>10,}")

# 中京1Rのデータソースを確認
print("\n" + "=" * 80)
print("中京1R (202512060701) の詳細")
print("=" * 80)

c.execute('''
    SELECT MIN(time_stamp), MAX(time_stamp), COUNT(*), COUNT(DISTINCT time_stamp)
    FROM odds_history
    WHERE race_id = '202512060701'
''')
result = c.fetchone()
print(f"時刻範囲: {result[0]} ～ {result[1]}")
print(f"総レコード数: {result[2]:,}")
print(f"時刻ポイント数: {result[3]}")

# オッズが0でないレコード数
c.execute('''
    SELECT COUNT(*)
    FROM odds_history
    WHERE race_id = '202512060701' AND odds_tan > 0
''')
non_zero = c.fetchone()[0]
print(f"オッズ > 0 のレコード数: {non_zero:,}")

# サンプルデータ（オッズが0でないもの）
print("\nオッズが入っているサンプルデータ（最初の10件）:")
c.execute('''
    SELECT time_stamp, umaban, odds_tan, odds_fuku_min, odds_fuku_max
    FROM odds_history
    WHERE race_id = '202512060701' AND odds_tan > 0
    ORDER BY time_stamp, umaban
    LIMIT 10
''')
print(f"{'時刻':<20} {'馬番':>4} {'単勝':>8} {'複勝Lo':>8} {'複勝Hi':>8}")
print("-" * 60)
for row in c.fetchall():
    print(f"{row[0]:<20} {row[1]:>4} {row[2]:>8.1f} {row[3]:>8.1f} {row[4]:>8.1f}")

# ターゲットからインポートしたデータかJV-Linkで取得したデータか判別
print("\n" + "=" * 80)
print("データソースの判別")
print("=" * 80)

# popularityが0のレコード数（ターゲットCSVインポートの特徴）
c.execute('''
    SELECT COUNT(*)
    FROM odds_history
    WHERE race_id = '202512060701' AND popularity = 0
''')
popularity_zero = c.fetchone()[0]

# popularityが0でないレコード数（JV-Linkの特徴）
c.execute('''
    SELECT COUNT(*)
    FROM odds_history
    WHERE race_id = '202512060701' AND popularity > 0
''')
popularity_non_zero = c.fetchone()[0]

print(f"popularity = 0 のレコード数: {popularity_zero:,} (ターゲットCSVインポート)")
print(f"popularity > 0 のレコード数: {popularity_non_zero:,} (JV-Link取得)")

if popularity_zero > 0 and popularity_non_zero == 0:
    print("\n→ このデータは「ターゲットCSVからインポート」されたものです")
elif popularity_non_zero > 0 and popularity_zero == 0:
    print("\n→ このデータは「JV-Linkで取得」されたものです")
else:
    print("\n→ 混在しています")

conn.close()
