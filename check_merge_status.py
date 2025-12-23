"""
JV-LinkデータとターゲットCSVデータのマージ状況を確認
"""
import sqlite3

conn = sqlite3.connect('data/odds_history.db')
c = conn.cursor()

race_id = '202512060701'

print("=" * 80)
print(f"中京1R ({race_id}) のデータマージ状況")
print("=" * 80)

# データソース別の統計
c.execute('''
    SELECT 
        CASE WHEN popularity = 0 THEN 'ターゲットCSV' ELSE 'JV-Link' END as source,
        COUNT(*) as total,
        COUNT(DISTINCT time_stamp) as time_points,
        MIN(time_stamp) as first_time,
        MAX(time_stamp) as last_time
    FROM odds_history
    WHERE race_id = ?
    GROUP BY source
''', (race_id,))

print(f"\n{'データソース':<15} {'レコード数':>10} {'時刻数':>8} {'最初':<20} {'最後':<20}")
print("-" * 80)
for row in c.fetchall():
    print(f"{row[0]:<15} {row[1]:>10,} {row[2]:>8} {row[3]:<20} {row[4]:<20}")

# 同じ時刻に両方のデータが存在するか確認
print("\n" + "=" * 80)
print("同じ時刻での重複状況")
print("=" * 80)

c.execute('''
    SELECT 
        time_stamp,
        SUM(CASE WHEN popularity = 0 THEN 1 ELSE 0 END) as target_count,
        SUM(CASE WHEN popularity > 0 THEN 1 ELSE 0 END) as jvlink_count
    FROM odds_history
    WHERE race_id = ?
    GROUP BY time_stamp
    HAVING target_count > 0 AND jvlink_count > 0
    ORDER BY time_stamp
    LIMIT 10
''', (race_id,))

overlap_times = c.fetchall()

if overlap_times:
    print(f"\n重複している時刻（最初の10個）:")
    print(f"{'時刻':<20} {'ターゲット':>10} {'JV-Link':>10}")
    print("-" * 50)
    for row in overlap_times:
        print(f"{row[0]:<20} {row[1]:>10} {row[2]:>10}")
    
    # 重複時刻の総数
    c.execute('''
        SELECT COUNT(DISTINCT time_stamp)
        FROM (
            SELECT time_stamp
            FROM odds_history
            WHERE race_id = ?
            GROUP BY time_stamp
            HAVING SUM(CASE WHEN popularity = 0 THEN 1 ELSE 0 END) > 0 
               AND SUM(CASE WHEN popularity > 0 THEN 1 ELSE 0 END) > 0
        )
    ''', (race_id,))
    total_overlap = c.fetchone()[0]
    print(f"\n重複時刻の総数: {total_overlap} 個")
    
    # 具体例: ある時刻での両方のデータを比較
    sample_time = overlap_times[5][0] if len(overlap_times) > 5 else overlap_times[0][0]
    
    print(f"\n" + "=" * 80)
    print(f"具体例: {sample_time} の馬番1のデータ比較")
    print("=" * 80)
    
    c.execute('''
        SELECT 
            CASE WHEN popularity = 0 THEN 'ターゲット' ELSE 'JV-Link' END as source,
            umaban, odds_tan, odds_fuku_min, odds_fuku_max, popularity
        FROM odds_history
        WHERE race_id = ? AND time_stamp = ? AND umaban = 1
        ORDER BY popularity
    ''', (race_id, sample_time))
    
    print(f"{'ソース':<12} {'馬番':>4} {'単勝':>8} {'複勝Lo':>8} {'複勝Hi':>8} {'人気':>4}")
    print("-" * 60)
    for row in c.fetchall():
        print(f"{row[0]:<12} {row[1]:>4} {row[2]:>8.1f} {row[3]:>8.1f} {row[4]:>8.1f} {row[5]:>4}")
else:
    print("\n→ 重複している時刻はありません（データが完全に分離されています）")

# 問題点の分析
print("\n" + "=" * 80)
print("マージの問題点")
print("=" * 80)

print("""
現状の問題:
1. 同じレース・同じ時刻・同じ馬番に対して、複数のレコードが存在
2. ターゲットCSVとJV-Linkのデータが重複して保存されている
3. データを取り出す際に、どちらを使うべきか判断が必要

推奨される対応:
1. データ取得時に重複チェックを行う
2. 既存データがある場合は上書きまたはスキップ
3. または、データソースの優先順位を決める（例: ターゲットCSV優先）
""")

conn.close()
