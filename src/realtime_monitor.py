"""
リアルタイムオッズ監視モジュール
JV-LinkのJVRTOpenを使用してリアルタイムでオッズ変動を監視する
"""
import win32com.client
import time
from parser import JVDataParser
import os
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

DB_PATH = 'data/odds_history.db'

class RealtimeOddsMonitor:
    """リアルタイムオッズ監視クラス"""
    
    def __init__(self, service_key="UNKNOWN"):
        self.service_key = service_key
        self.jvlink = None
        self.is_monitoring = False
        
    def connect(self):
        """JV-Linkへの接続"""
        try:
            print("JV-Linkに接続中...")
            self.jvlink = win32com.client.Dispatch("JVDTLab.JVLink")
            result = self.jvlink.JVInit(self.service_key)
            
            if result == 0:
                print("[OK] JV-Link接続成功")
                return True
            elif result == -1:
                print("[WARNING] サービスキーが未設定です")
                return False
            else:
                print(f"JVInit結果: {result}")
                return False
                
        except Exception as e:
            print(f"[ERROR] 接続エラー: {e}")
            return False
    
    def start_monitoring(self, data_types="0B31"):
        """
        リアルタイム監視開始
        Args:
            data_types: 監視するデータ種別
                0B31 = オッズ（単勝・複勝）リアルタイム
                0B32 = オッズ（枠連）
                0B33 = オッズ（馬連）
                0B34 = オッズ（ワイド）
                0B35 = オッズ（馬単）
                0B36 = オッズ（3連複）
                0B37 = オッズ（3連単）
        """
        if not self.jvlink:
            print("[ERROR] JV-Linkが初期化されていません")
            return
        
        print(f"\nリアルタイム監視開始: データ種別 {data_types}")
        
        try:
            # JVRTOpen - リアルタイム監視開始
            # 0B12(速報オッズ)は開催日(YYYYMMDD)の指定が必須
            from datetime import datetime
            key = datetime.now().strftime("%Y%m%d")
            print(f"  → 監視対象日: {key}")
            
            result = self.jvlink.JVRTOpen(data_types, key)
            
            if result == 0:
                print("[OK] リアルタイム監視開始成功")
                self.is_monitoring = True
                self._monitor_loop()
            else:
                print(f"[ERROR] リアルタイム監視開始失敗: エラーコード {result}")
                
        except Exception as e:
            print(f"[ERROR] 監視開始エラー: {e}")
    
    def _monitor_loop(self):
        """監視ループ"""
        print("\nオッズ更新を監視中... (Ctrl+Cで終了)")
        parser = JVDataParser(DB_PATH)
        
        try:
            while self.is_monitoring:
                # 速報系では JVGets を必ず使用（JVReadは暴走の可能性あり）
                buff_size = 50000
                buff = bytearray(buff_size)
                
                # JVGets でデータ取得（速報系で安全）
                # 戻り値: (code, data) のタプル
                ret = self.jvlink.JVGets(buff, buff_size)
                
                # タプルの場合は最初の要素がコード
                if isinstance(ret, tuple):
                    result = ret[0]
                    data_blob = ret[1] if len(ret) > 1 else None
                else:
                    result = ret
                    data_blob = None
                
                if result == 0:
                    # データなし、少し待機
                    time.sleep(1)
                    continue
                elif result == -1:
                    # ファイル切り替え
                    print(f"  ファイル切り替え")
                    continue
                elif result > 0:
                    # データ取得成功
                    # byte配列から文字列にデコード
                    if data_blob:
                        # memoryview を bytes に変換してからデコード
                        data = bytes(data_blob).decode('shift_jis', errors='ignore')
                    else:
                        data = buff[:result].decode('shift_jis', errors='ignore')
                    
                    # レコードタイプを判定（先頭2文字）
                    rec_type = data[:2] if len(data) >= 2 else "??"
                    
                    # レコードタイプごとのラベル
                    type_labels = {
                        "O1": "単勝オッズ",
                        "O2": "複勝オッズ",
                        "O3": "枠連オッズ",
                        "O4": "馬連オッズ",
                        "O5": "ワイドオッズ",
                        "O6": "馬単オッズ",
                        "SE": "成績データ",
                        "RA": "レース情報",
                        "HR": "払戻金",
                        "JC": "騎手変更",
                        "TC": "調教師変更",
                    }
                    label = type_labels.get(rec_type, f"不明({rec_type})")
                    
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{timestamp}] 受信: {label}")
                    
                    # レコードタイプに応じて処理
                    if rec_type.startswith("O"):
                        parser.parse_odds_record(data.encode('shift_jis'), rec_type)
                        parser.commit()
                else:
                    print(f"[ERROR] JVGets エラー: {result}")
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            print("\n\n監視を停止します...")
        except Exception as e:
            print(f"[ERROR] 監視エラー: {e}")
        finally:
            parser.close()
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """監視停止"""
        if self.jvlink and self.is_monitoring:
            try:
                self.jvlink.JVClose()
                self.is_monitoring = False
                print("[OK] リアルタイム監視を停止しました")
            except Exception as e:
                print(f"[ERROR] 監視停止エラー: {e}")

def main():
    """メイン処理"""
    print("=" * 60)
    print("リアルタイムオッズ監視ツール")
    print("=" * 60)
    
    import os
    service_key = os.getenv("JRAVAN_SERVICE_KEY", "UNKNOWN")
    
    # Debug: Key Status
    if service_key == "UNKNOWN":
        print("⚠ 環境変数 JRAVAN_SERVICE_KEY が設定されていません。")
        print("  デフォルト値 'UNKNOWN' で接続を試みます。")
    else:
        print(f"環境変数 JRAVAN_SERVICE_KEY を検出しました (Len: {len(service_key)})")
        # キーの整形: 空白除去とハイフン除去
        service_key = service_key.strip().replace('-', '')
        print(f"  → 整形後キー: {service_key[:4]}...{service_key[-4:]} (Len: {len(service_key)})")
    
    monitor = RealtimeOddsMonitor(service_key)
    
    if monitor.connect():
        # 単勝・複勝オッズを監視
        monitor.start_monitoring("0B12")
    else:
        print("接続に失敗しました")

if __name__ == '__main__':
    main()
