"""
JV-Data パーサー
JV-Dataフォーマットからレース情報とオッズデータを抽出する
"""
import sqlite3
from datetime import datetime

class JVDataParser:
    """JV-Dataレコードのパーサー"""
    
    def __init__(self, db_path='data/odds_history.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        # WALモードを有効化（書き込み性能向上、ロック競合軽減）
        self.cursor.execute("PRAGMA journal_mode=WAL")
        self.cursor.execute("PRAGMA synchronous=NORMAL")
    
    def _safe_float(self, val_str):
        """文字列を安全にfloatに変換する（非数値は0.0）"""
        try:
            if not val_str:
                return 0.0
            # 記号を除去
            clean_str = val_str.strip().replace('*', '').replace('-', '').replace(' ', '')
            if not clean_str:
                return 0.0
            return float(clean_str)
        except:
            return 0.0

    def _safe_int(self, val_str):
        """文字列を安全にintに変換する（非数値は0）"""
        try:
            if not val_str:
                return 0
            # 記号を除去
            clean_str = val_str.strip().replace('*', '').replace('-', '').replace(' ', '')
            if not clean_str:
                return 0
            return int(clean_str)
        except:
            return 0

    def parse_race_record(self, data):
        """
        RAレコード（レース詳細）をパース
        JV-Data仕様書 Ver4.9.0に基づく
        引数 data は bytes 型であることを想定
        """
        try:
            # RAレコードの基本構造
            
            # バイト列として処理
            rec_type = data[0:2].decode('ascii', errors='ignore')
            if rec_type != "RA":
                return
            
            # すべてShift_JISとしてデコードを試みる方が安全
            race_key_year = data[11:15].decode('ascii', errors='ignore')
            race_key_month = data[15:17].decode('ascii', errors='ignore')
            race_key_day = data[17:19].decode('ascii', errors='ignore')
            race_key_ba = data[19:21].decode('ascii', errors='ignore')  # 場コード
            race_key_kai = data[21:23].decode('ascii', errors='ignore')
            race_key_nichi = data[23:25].decode('ascii', errors='ignore')
            race_key_race_no = data[25:27].decode('ascii', errors='ignore')
            
            race_id = f"{race_key_year}{race_key_month}{race_key_day}{race_key_ba}{race_key_race_no}"
            race_date = f"{race_key_year}-{race_key_month}-{race_key_day}"
            
            # レース名: オフセット32付近から。
            race_name_bytes = data[32:96] 
            try:
                # ヌルバイトを事前に除去してからデコード
                race_name_bytes = race_name_bytes.replace(b'\x00', b'')
                race_name = race_name_bytes.decode('shift_jis', errors='replace')
                # 全角スペース、半角スペースを除去
                race_name = race_name.replace('\u3000', ' ').strip()
            except:
                race_name = "不明なレース"
            
            # 発走時刻（58-61の4バイト HHMM形式）
            start_time_str = data[58:62].decode('ascii', errors='ignore').strip()
            if len(start_time_str) == 4 and start_time_str.isdigit():
                start_time = f"{start_time_str[0:2]}:{start_time_str[2:4]}"
            else:
                start_time = "00:00"
            
            # データベースに保存
            self.cursor.execute('''
                INSERT OR REPLACE INTO races (race_id, date, ba_code, race_no, race_name, start_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (race_id, race_date, race_key_ba, self._safe_int(race_key_race_no), race_name, start_time))
            print(f"  [DB] レース情報保存: {race_id} ({race_name})")
            
        except Exception as e:
            print(f"  [ERROR] RAレコードパースエラー: {e}")
    
    def parse_odds_record(self, data, rec_type):
        """
        オッズレコード（O1-O6）をパース
        v0.82: オッズ1(単複枠)レコードから単勝部と複勝部の両方を解析
        """
        try:
            if rec_type.startswith("O1"):
                # オッズ1(単複枠)レコード: 単勝部と複勝部の両方を解析
                self._parse_tansho_odds(data)
                self._parse_fukusho_odds(data)
            # 他のオッズタイプも同様に実装可能
                
        except Exception as e:
            print(f"  [ERROR] オッズレコードパースエラー ({rec_type}): {e}")
    
    def _parse_tansho_odds(self, data):
        """
        オッズ1レコードの単勝オッズ部をパース
        v0.82: 複勝オッズ部は _parse_fukusho_odds() で別途解析
        """
        try:
            # レースキー取得（RAと同じオフセット11）
            race_key_year = data[11:15].decode('ascii', errors='ignore')
            race_key_month = data[15:17].decode('ascii', errors='ignore')
            race_key_day = data[17:19].decode('ascii', errors='ignore')
            race_key_ba = data[19:21].decode('ascii', errors='ignore')
            race_key_race_no = data[25:27].decode('ascii', errors='ignore')
            
            race_id = f"{race_key_year}{race_key_month}{race_key_day}{race_key_ba}{race_key_race_no}"
            
            # 発表時刻 (月日時分) Offset 27-35 (8バイト: MMDDHHMM)
            try:
                ann_month = data[27:29].decode('ascii', errors='ignore')
                ann_day = data[29:31].decode('ascii', errors='ignore')
                ann_hour = data[31:33].decode('ascii', errors='ignore')
                ann_min = data[33:35].decode('ascii', errors='ignore')
                
                timestamp = f"{race_key_year}-{ann_month}-{ann_day} {ann_hour}:{ann_min}"
            except:
                timestamp = f"{race_key_year}-{race_key_month}-{race_key_day} 00:00"
            
            # 単勝オッズ部: オフセット43から開始、1頭あたり8バイト
            # [馬番2][単勝4][人気2]
            offset = 43
            
            for i in range(28):
                umaban_str = data[offset:offset+2].decode('ascii', errors='ignore').strip()
                if not umaban_str:
                    break
                umaban = self._safe_int(umaban_str)
                if umaban == 0:
                    break
                
                # 単勝オッズ (4バイト、10倍値)
                tansho_str = data[offset+2:offset+6].decode('ascii', errors='ignore').strip()
                tansho_odds = self._safe_float(tansho_str) / 10
                
                # 人気順 (2バイト)
                popularity_str = data[offset+6:offset+8].decode('ascii', errors='ignore').strip()
                popularity = self._safe_int(popularity_str)
                
                # データベースに保存(複勝は0.0、後で_parse_fukusho_oddsがUPDATE)
                self.cursor.execute('''
                    INSERT INTO odds_history 
                    (race_id, time_stamp, umaban, odds_tan, odds_fuku_min, odds_fuku_max, popularity)
                    VALUES (?, ?, ?, ?, 0.0, 0.0, ?)
                    ON CONFLICT(race_id, time_stamp, umaban) DO UPDATE SET
                    odds_tan = excluded.odds_tan,
                    popularity = excluded.popularity
                ''', (race_id, timestamp, umaban, tansho_odds, popularity))
                
                offset += 8
            
        except Exception as e:
            print(f"  [ERROR] 単勝オッズパースエラー: {e}")
    
    def _parse_fukusho_odds(self, data):
        """
        オッズ1レコードの複勝オッズ部をパース
        v0.82: 新規追加。JV-Data仕様書 Ver 4.9.0.1 に基づく実装。
        """
        try:
            # レースキー取得(単勝部と同じ)
            race_key_year = data[11:15].decode('ascii', errors='ignore')
            race_key_month = data[15:17].decode('ascii', errors='ignore')
            race_key_day = data[17:19].decode('ascii', errors='ignore')
            race_key_ba = data[19:21].decode('ascii', errors='ignore')
            race_key_race_no = data[25:27].decode('ascii', errors='ignore')
            
            race_id = f"{race_key_year}{race_key_month}{race_key_day}{race_key_ba}{race_key_race_no}"
            
            # 発表時刻取得(単勝部と同じ)
            try:
                ann_month = data[27:29].decode('ascii', errors='ignore')
                ann_day = data[29:31].decode('ascii', errors='ignore')
                ann_hour = data[31:33].decode('ascii', errors='ignore')
                ann_min = data[33:35].decode('ascii', errors='ignore')
                
                timestamp = f"{race_key_year}-{ann_month}-{ann_day} {ann_hour}:{ann_min}"
            except:
                timestamp = f"{race_key_year}-{race_key_month}-{race_key_day} 00:00"
            
            # 複勝オッズ部の開始位置を計算
            # 単勝部: オフセット43 + (28頭 × 8バイト) = 267
            TANSHO_START = 43
            UMA_MAX = 28
            FUKUSHO_START = TANSHO_START + (UMA_MAX * 8)  # = 267
            
            # デバッグ: レコードヘッダーを確認
            if race_id == "202512210909":
                rec_type_id = data[0:2].decode('ascii', errors='ignore')
                data_kbn = data[2:3].decode('ascii', errors='ignore')
                print(f"\nDEBUG レコード [{race_id}]:")
                print(f"  レコード種別ID: '{rec_type_id}'")
                print(f"  データ区分: '{data_kbn}'")
                print(f"  レコード長: {len(data)} bytes")
                print(f"  ヘッダー(0-43): {data[0:43].hex()}")
            
            # 馬番ごとのオッズ(1頭あたり10バイト)
            # [馬番2][複勝下限4][複勝上限4]
            offset = FUKUSHO_START
            
            for i in range(UMA_MAX):
                if offset + 10 > len(data):
                    break

                # 馬番 (2バイト)
                umaban_str = data[offset:offset+2].decode('ascii', errors='ignore').strip()
                if not umaban_str or not umaban_str.isdigit():
                    # 馬番が数字でない、または空なら終了
                    break
                
                umaban = int(umaban_str)
                if umaban <= 0:
                    break
                
                # 複勝オッズ下限 (4バイト、10倍値)
                fuku_min_val = self._safe_float(data[offset+2:offset+6].decode('ascii', errors='ignore'))
                fuku_min = fuku_min_val / 10.0
                
                # 複勝オッズ上限 (4バイト、10倍値)
                fuku_max_val = self._safe_float(data[offset+6:offset+10].decode('ascii', errors='ignore'))
                fuku_max = fuku_max_val / 10.0
                
                # 異常値チェック (未発表や異常データ)
                if fuku_min > fuku_max and fuku_max > 0:
                    # 入れ替わっている、または異常値の場合はスキップまたは補正
                    continue

                # データベースに保存(単勝部で既にINSERTされているのでUPDATE)
                self.cursor.execute('''
                    INSERT INTO odds_history 
                    (race_id, time_stamp, umaban, odds_tan, odds_fuku_min, odds_fuku_max, popularity)
                    VALUES (?, ?, ?, 0.0, ?, ?, 0)
                    ON CONFLICT(race_id, time_stamp, umaban) DO UPDATE SET
                    odds_fuku_min = excluded.odds_fuku_min,
                    odds_fuku_max = excluded.odds_fuku_max
                ''', (race_id, timestamp, umaban, fuku_min, fuku_max))
                
                offset += 10
            
        except Exception as e:
            print(f"  [ERROR] 複勝オッズパースエラー: {e}")
    
    def commit(self):
        """変更をコミット"""
        if self.conn:
            self.conn.commit()
    
    def close(self):
        """接続を閉じる"""
        if self.conn:
            self.conn.close()
