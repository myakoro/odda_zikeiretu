import sqlite3

db_path = 'data/odds_history.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # テーブル構造を確認
    cursor.execute("PRAGMA table_info(odds_history)")
    columns = cursor.fetchall()
    print("odds_history テーブルの構造:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # サンプルデータを取得
    print("\n最新5件のオッズデータ:")
    cursor.execute("SELECT * FROM odds_history ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    
    if rows:
        for row in rows:
            print(f"  {row}")
    else:
        print("  データなし")
    
    # レコード種別を確認（もしrec_typeカラムがあれば）
    cursor.execute("PRAGMA table_info(odds_history)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'rec_type' in columns:
        cursor.execute("SELECT DISTINCT rec_type FROM odds_history")
        rec_types = cursor.fetchall()
        print("\n存在するレコードタイプ:")
        for rt in rec_types:
            print(f"  {rt[0]}")
    
    conn.close()
    
except Exception as e:
    print(f"エラー: {e}")
