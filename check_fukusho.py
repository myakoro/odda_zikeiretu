"""
複勝オッズが入っているデータを確認
"""
import sqlite3

conn = sqlite3.connect('data/odds_history.db')
c = conn.cursor()

race_id = '202512060703'

print("=" * 80)
print(f"中京3R ({race_id}) の複勝オッズ確認")
print("=" * 80)

# 複勝オッズが0でないレコード数
c.execute('''
    SELECT COUNT(*)
    FROM odds_history
    WHERE race_id = ? AND (odds_fuku_min > 0 OR odds_fuku_max > 0)
''', (race_id,))
fuku_non_zero = c.fetchone()[0]

print(f"\n複勝オッズ > 0 のレコード数: {fuku_non_zero:,}")

# 複勝オッズが入っているサンプルデータ
if fuku_non_zero > 0:
    print(f"\n複勝オッズが入っているデータ（最初の20件）:")
    print(f"{'時刻':<20} {'馬番':>4} {'単勝':>8} {'複勝Lo':>8} {'複勝Hi':>8}")
    print("-" * 70)
    
    c.execute('''
        SELECT time_stamp, umaban, odds_tan, odds_fuku_min, odds_fuku_max
        FROM odds_history
        WHERE race_id = ? AND (odds_fuku_min > 0 OR odds_fuku_max > 0)
        ORDER BY time_stamp, umaban
        LIMIT 20
    ''', (race_id,))
    
    for row in c.fetchall():
        print(f"{row[0]:<20} {row[1]:>4} {row[2]:>8.1f} {row[3]:>8.1f} {row[4]:>8.1f}")
else:
    print("\n→ 複勝オッズが入っているデータがありません")
    print("\nこれはJV-Linkのデータ取得時の問題の可能性があります。")
    print("JV-Linkで時系列オッズ（0B41）を取得する際、複勝オッズが含まれていない場合があります。")

# 他のレースで複勝オッズが入っているか確認
print("\n" + "=" * 80)
print("他のレースの複勝オッズ状況（12月6日）")
print("=" * 80)

c.execute('''
    SELECT 
        r.race_id,
        r.ba_code,
        r.race_no,
        COUNT(o.id) as total_records,
        SUM(CASE WHEN o.odds_fuku_min > 0 OR o.odds_fuku_max > 0 THEN 1 ELSE 0 END) as fuku_records
    FROM races r
    LEFT JOIN odds_history o ON r.race_id = o.race_id
    WHERE r.date = '2025-12-06' AND r.ba_code = '07'
    GROUP BY r.race_id
    ORDER BY r.race_id
    LIMIT 10
''')

print(f"{'レースID':<15} {'場':<4} {'R':<3} {'総レコード':>10} {'複勝あり':>10}")
print("-" * 50)
for row in c.fetchall():
    print(f"{row[0]:<15} {row[1]:<4} {row[2]:<3} {row[3]:>10,} {row[4]:>10,}")

conn.close()
