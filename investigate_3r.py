"""
中京3Rのデータを詳しく調査
"""
import sqlite3

conn = sqlite3.connect('data/odds_history.db')
c = conn.cursor()

race_id = '202512060703'

print("=" * 80)
print(f"中京3R ({race_id}) の詳細調査")
print("=" * 80)

# 総レコード数
c.execute('SELECT COUNT(*) FROM odds_history WHERE race_id = ?', (race_id,))
total = c.fetchone()[0]
print(f"\n総レコード数: {total:,}")

# オッズが0のレコード数
c.execute('SELECT COUNT(*) FROM odds_history WHERE race_id = ? AND odds_tan = 0', (race_id,))
zero_odds = c.fetchone()[0]
print(f"オッズ = 0 のレコード数: {zero_odds:,}")

# オッズが0でないレコード数
c.execute('SELECT COUNT(*) FROM odds_history WHERE race_id = ? AND odds_tan > 0', (race_id,))
non_zero_odds = c.fetchone()[0]
print(f"オッズ > 0 のレコード数: {non_zero_odds:,}")

# データソース確認
c.execute('SELECT COUNT(*) FROM odds_history WHERE race_id = ? AND popularity = 0', (race_id,))
target_import = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM odds_history WHERE race_id = ? AND popularity > 0', (race_id,))
jvlink_data = c.fetchone()[0]

print(f"\nデータソース:")
print(f"  popularity = 0 (ターゲットCSV): {target_import:,}")
print(f"  popularity > 0 (JV-Link): {jvlink_data:,}")

# オッズが0でないデータのサンプル
print(f"\n" + "=" * 80)
print("オッズ > 0 のデータ（最初の20件）:")
print("=" * 80)
c.execute('''
    SELECT time_stamp, umaban, odds_tan, odds_fuku_min, odds_fuku_max, popularity
    FROM odds_history
    WHERE race_id = ? AND odds_tan > 0
    ORDER BY time_stamp, umaban
    LIMIT 20
''', (race_id,))

results = c.fetchall()
if results:
    print(f"{'時刻':<20} {'馬番':>4} {'単勝':>8} {'複勝Lo':>8} {'複勝Hi':>8} {'人気':>4}")
    print("-" * 70)
    for row in results:
        print(f"{row[0]:<20} {row[1]:>4} {row[2]:>8.1f} {row[3]:>8.1f} {row[4]:>8.1f} {row[5]:>4}")
else:
    print("→ オッズ > 0 のデータがありません")

# オッズが0のデータのサンプル
print(f"\n" + "=" * 80)
print("オッズ = 0 のデータ（最初の20件）:")
print("=" * 80)
c.execute('''
    SELECT time_stamp, umaban, odds_tan, odds_fuku_min, odds_fuku_max, popularity
    FROM odds_history
    WHERE race_id = ? AND odds_tan = 0
    ORDER BY time_stamp, umaban
    LIMIT 20
''', (race_id,))

results = c.fetchall()
if results:
    print(f"{'時刻':<20} {'馬番':>4} {'単勝':>8} {'複勝Lo':>8} {'複勝Hi':>8} {'人気':>4}")
    print("-" * 70)
    for row in results:
        print(f"{row[0]:<20} {row[1]:>4} {row[2]:>8.1f} {row[3]:>8.1f} {row[4]:>8.1f} {row[5]:>4}")

# 時刻ごとのオッズ状況
print(f"\n" + "=" * 80)
print("時刻ごとのオッズ状況（最初の10時刻）:")
print("=" * 80)
c.execute('''
    SELECT 
        time_stamp,
        COUNT(*) as total,
        SUM(CASE WHEN odds_tan > 0 THEN 1 ELSE 0 END) as non_zero,
        SUM(CASE WHEN odds_tan = 0 THEN 1 ELSE 0 END) as zero
    FROM odds_history
    WHERE race_id = ?
    GROUP BY time_stamp
    ORDER BY time_stamp
    LIMIT 10
''', (race_id,))

print(f"{'時刻':<20} {'総数':>6} {'オッズ>0':>8} {'オッズ=0':>8}")
print("-" * 50)
for row in c.fetchall():
    print(f"{row[0]:<20} {row[1]:>6} {row[2]:>8} {row[3]:>8}")

conn.close()
