import csv

csv_path = r'C:\Users\takuy\Desktop\投資競馬アプリ系\時系列オッズ取得アプリ\target系\JD07255101.CSV'

with open(csv_path, 'r', encoding='shift_jis') as f:
    reader = csv.reader(f)
    
    # ヘッダー
    header = next(reader)
    print(f"Total columns: {len(header)}")
    print(f"\nHeader columns:")
    for i, col in enumerate(header):
        print(f"  {i}: {col}")
    
    # 最初の3行
    print(f"\n\nFirst 3 data rows:")
    for i, row in enumerate(reader):
        if i >= 3:
            break
        print(f"\nRow {i+1}:")
        print(f"  レースID: {row[0]}")
        print(f"  区分: {row[1]}")
        print(f"  月日時分: {row[2]}")
        print(f"  頭数: {row[3]}")
        print(f"  単勝票数: {row[4]}")
        print(f"  複勝票数: {row[5]}")
        print(f"  1単: {row[6]}")
        print(f"  1複Lo: {row[7]}")
        print(f"  1複Hi: {row[8]}")
        print(f"  2単: {row[9]}")
        print(f"  (showing first 10 fields only...)")
    
    # 総行数
    count = 3
    for row in reader:
        count += 1
    
    print(f"\n\nTotal rows (including header): {count + 1}")
