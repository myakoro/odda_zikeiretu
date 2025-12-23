"""
ターゲットからエクスポートしたCSVファイルをインポートするスクリプト

使い方:
    python src/import_from_target.py target系/JD07255101.CSV
    python src/import_from_target.py target系/*.CSV  # 複数ファイル一括インポート
"""

import csv
import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime
import glob


class TargetCSVImporter:
    """ターゲットCSVインポーター"""
    
    def __init__(self, db_path='data/odds_history.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # 統計情報
        self.stats = {
            'files_processed': 0,
            'races_imported': 0,
            'odds_records_imported': 0,
            'errors': 0
        }
    
    def parse_race_id(self, race_id_str):
        """
        レースIDをパース
        例: 2025120607050101 -> (2025-12-06, 07, 05, 01)
        """
        try:
            year = race_id_str[0:4]
            month = race_id_str[4:6]
            day = race_id_str[6:8]
            ba_code = race_id_str[8:10]
            kai = race_id_str[10:12]
            race_no = race_id_str[12:14]
            
            race_date = f"{year}-{month}-{day}"
            
            # 標準レースID形式に変換 (YYYYMMDDBBRRR)
            standard_race_id = f"{year}{month}{day}{ba_code}{race_no}"
            
            return {
                'race_id': standard_race_id,
                'date': race_date,
                'ba_code': ba_code,
                'race_no': int(race_no),
                'kai': kai
            }
        except Exception as e:
            print(f"[ERROR] レースIDパースエラー: {race_id_str} - {e}")
            return None
    
    def parse_timestamp(self, race_info, time_str):
        """
        月日時分を完全なタイムスタンプに変換
        例: 12051831 -> 2025-12-05 18:31
        """
        try:
            month = time_str[0:2]
            day = time_str[2:4]
            hour = time_str[4:6]
            minute = time_str[6:8]
            
            # レース日から年を取得
            year = race_info['date'].split('-')[0]
            
            timestamp = f"{year}-{month}-{day} {hour}:{minute}"
            return timestamp
        except Exception as e:
            print(f"[ERROR] タイムスタンプパースエラー: {time_str} - {e}")
            return None
    
    def get_ba_name(self, ba_code):
        """競馬場コードから競馬場名を取得"""
        ba_map = {
            '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
            '05': '東京', '06': '中山', '07': '中京', '08': '京都',
            '09': '阪神', '10': '小倉'
        }
        return ba_map.get(ba_code, f'場コード{ba_code}')
    
    def import_csv(self, csv_path):
        """
        ターゲットCSVファイルをインポート
        """
        print(f"\n{'='*60}")
        print(f"インポート開始: {csv_path}")
        print(f"{'='*60}")
        
        if not os.path.exists(csv_path):
            print(f"[ERROR] ファイルが見つかりません: {csv_path}")
            self.stats['errors'] += 1
            return False
        
        try:
            with open(csv_path, 'r', encoding='shift_jis') as f:
                reader = csv.DictReader(f)
                
                race_info = None
                records_count = 0
                
                for row in reader:
                    # レース情報を取得（最初の行で取得）
                    if race_info is None:
                        race_info = self.parse_race_id(row['レースID'])
                        if race_info is None:
                            print(f"[ERROR] レースID解析失敗")
                            self.stats['errors'] += 1
                            return False
                        
                        # レース情報をDBに保存
                        ba_name = self.get_ba_name(race_info['ba_code'])
                        race_name = f"{ba_name} {race_info['race_no']}R"
                        
                        self.cursor.execute('''
                            INSERT OR REPLACE INTO races (race_id, date, ba_code, race_no, race_name, start_time)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            race_info['race_id'],
                            race_info['date'],
                            race_info['ba_code'],
                            race_info['race_no'],
                            race_name,
                            '00:00'  # ターゲットCSVには発走時刻が含まれていない
                        ))
                        
                        print(f"レース情報: {race_name} ({race_info['date']})")
                        self.stats['races_imported'] += 1
                    
                    # タイムスタンプを取得
                    timestamp = self.parse_timestamp(race_info, row['月日時分'])
                    if timestamp is None:
                        continue
                    
                    # 頭数を取得
                    tosu = int(row['頭数'])
                    
                    # 各馬番のオッズをインポート
                    for umaban in range(1, tosu + 1):
                        try:
                            # カラム名: "1単", "1複Lo", "1複Hi"
                            tan_col = f"{umaban}単"
                            fuku_lo_col = f"{umaban}複Lo"
                            fuku_hi_col = f"{umaban}複Hi"
                            
                            # オッズ値を取得
                            odds_tan = float(row.get(tan_col, 0.0))
                            odds_fuku_min = float(row.get(fuku_lo_col, 0.0))
                            odds_fuku_max = float(row.get(fuku_hi_col, 0.0))
                            
                            # オッズが0の場合はスキップ（データなし）
                            if odds_tan == 0.0 and odds_fuku_min == 0.0:
                                continue
                            
                            # データベースに保存
                            # v0.82: ON CONFLICT句を追加してUNIQUE制約に対応
                            self.cursor.execute('''
                                INSERT INTO odds_history 
                                (race_id, time_stamp, umaban, odds_tan, odds_fuku_min, odds_fuku_max, popularity)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT(race_id, time_stamp, umaban) DO UPDATE SET
                                odds_tan = excluded.odds_tan,
                                odds_fuku_min = excluded.odds_fuku_min,
                                odds_fuku_max = excluded.odds_fuku_max
                            ''', (
                                race_info['race_id'],
                                timestamp,
                                umaban,
                                odds_tan,
                                odds_fuku_min,
                                odds_fuku_max,
                                0  # ターゲットCSVには人気順が含まれていない
                            ))
                            
                            records_count += 1
                            
                        except KeyError as e:
                            # 馬番が存在しない場合（頭数より多い馬番）
                            continue
                        except Exception as e:
                            print(f"[WARNING] 馬番{umaban}のデータ処理エラー: {e}")
                            continue
                
                # コミット
                self.conn.commit()
                
                print(f"✓ インポート完了: {records_count} 件のオッズレコード")
                self.stats['odds_records_imported'] += records_count
                self.stats['files_processed'] += 1
                
                return True
                
        except Exception as e:
            print(f"[ERROR] CSVインポートエラー: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1
            return False
    
    def import_directory(self, pattern):
        """
        ディレクトリ内の複数CSVファイルを一括インポート
        """
        files = glob.glob(pattern)
        
        if not files:
            print(f"[ERROR] パターンに一致するファイルが見つかりません: {pattern}")
            return
        
        print(f"\n{len(files)} 件のファイルが見つかりました")
        
        for csv_file in files:
            self.import_csv(csv_file)
        
        self.print_summary()
    
    def print_summary(self):
        """インポート結果のサマリーを表示"""
        print(f"\n{'='*60}")
        print(f"インポート完了サマリー")
        print(f"{'='*60}")
        print(f"処理ファイル数: {self.stats['files_processed']}")
        print(f"インポートレース数: {self.stats['races_imported']}")
        print(f"インポートオッズレコード数: {self.stats['odds_records_imported']:,}")
        print(f"エラー数: {self.stats['errors']}")
        print(f"{'='*60}\n")
    
    def close(self):
        """データベース接続を閉じる"""
        if self.conn:
            self.conn.close()


def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("使い方:")
        print("  python src/import_from_target.py <CSVファイルパス>")
        print("  python src/import_from_target.py target系/JD07255101.CSV")
        print("  python src/import_from_target.py target系/*.CSV")
        sys.exit(1)
    
    # インポーター初期化
    importer = TargetCSVImporter()
    
    try:
        # ファイルパターンを取得
        pattern = sys.argv[1]
        
        # ワイルドカードが含まれている場合は複数ファイル処理
        if '*' in pattern or '?' in pattern:
            importer.import_directory(pattern)
        else:
            # 単一ファイル処理
            success = importer.import_csv(pattern)
            if success:
                importer.print_summary()
    
    finally:
        importer.close()


if __name__ == '__main__':
    main()
