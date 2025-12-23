import sqlite3

conn = sqlite3.connect('data/odds_history.db')
c = conn.cursor()

# レース情報を確認
c.execute('SELECT * FROM races WHERE race_id LIKE "20251206%"')
print('=' * 60)
print('レース情報:')
print('=' * 60)
for row in c.fetchall():
    print(f'  ID: {row[0]}')
    print(f'  日付: {row[1]}')
    print(f'  競馬場: {row[2]}')
    print(f'  レース番号: {row[3]}')
    print(f'  レース名: {row[4]}')
    print(f'  発走時刻: {row[5]}')
    print()

# オッズレコード数を確認
c.execute('SELECT COUNT(*) FROM odds_history WHERE race_id LIKE "20251206%"')
count = c.fetchone()[0]
print('=' * 60)
print(f'オッズレコード総数: {count:,} 件')
print('=' * 60)

# 時系列データの範囲を確認
c.execute('''
    SELECT 
        MIN(time_stamp) as first_time,
        MAX(time_stamp) as last_time,
        COUNT(DISTINCT time_stamp) as time_points
    FROM odds_history 
    WHERE race_id LIKE "20251206%"
''')
time_range = c.fetchone()
print(f'\n時系列データ範囲:')
print(f'  最初: {time_range[0]}')
print(f'  最後: {time_range[1]}')
print(f'  時刻ポイント数: {time_range[2]} 個')

# サンプルデータを表示
print(f'\n' + '=' * 60)
print('サンプルデータ（最初の時刻、馬番1-5）:')
print('=' * 60)
c.execute('''
    SELECT time_stamp, umaban, odds_tan, odds_fuku_min, odds_fuku_max
    FROM odds_history 
    WHERE race_id LIKE "20251206%"
    ORDER BY time_stamp, umaban
    LIMIT 10
''')
for row in c.fetchall():
    print(f'  {row[0]} | 馬番{row[1]:2d} | 単勝:{row[2]:6.1f} | 複勝:{row[3]:5.1f}-{row[4]:5.1f}')

conn.close()
