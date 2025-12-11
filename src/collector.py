"""
JV-Link データ取得モジュール
過去オッズデータとリアルタイムオッズを取得してSQLiteに保存する
"""
import win32com.client
import sqlite3
import os
from datetime import datetime, timedelta
from parser import JVDataParser

DB_PATH = 'data/odds_history.db'

class JVLinkCollector:
    """JV-Linkを使用したデータ取得クラス"""
    
    def __init__(self, service_key="UNKNOWN"):
        """
        初期化
        Args:
            service_key: JRA-VANのサービスキー（契約時に取得）
        """
        self.service_key = service_key
        self.jvlink = None
        self.conn = None
        
    def connect(self):
        """JV-Linkへの接続とDB接続"""
        try:
            print("JV-Linkに接続中...")
            self.jvlink = win32com.client.Dispatch("JVDTLab.JVLink")
            
            # JVInitにサービスキーを渡す
            # .envから読み込んだキーを使用する
            result = self.jvlink.JVInit(self.service_key)
            
            if result == 0:
                print("[OK] JV-Link接続成功")
            elif result == -1:
                print("[WARNING] サービスキーが未設定です")
                print("  JV-Link設定ツールでサービスキーを登録してください。")
            elif result == -103:
                print("[ERROR] サービスキー認証エラー (-103)")
                print("  JV-Link設定ツールでサービスキーを確認してください。")
                print("  または、管理者権限で実行してください。")
            else:
                print(f"JVInit結果: {result}")
            
            # データベース接続
            self.conn = sqlite3.connect(DB_PATH)
            print(f"[OK] データベース接続: {DB_PATH}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 接続エラー: {e}")
            return False
    
    def fetch_historical_odds(self, start_date, end_date, data_spec="RACE"):
        """
        過去のオッズデータを取得
        Args:
            start_date: 開始日 (YYYYMMDD形式の文字列)
            end_date: 終了日 (YYYYMMDD形式の文字列)
            data_spec: データ種別 ("RACE"=確定のみ, "0B41"=時系列)
        """
        if not self.jvlink:
            print("[ERROR] JV-Linkが初期化されていません")
            return
        
        print(f"\n過去データ取得: {start_date} ～ {end_date} (Type={data_spec})")
        
        try:
            # 時系列取得(0B41)の場合は、JVOpenではなくJVRTOpenで1日ずつ取得する必要がある
            # (JRA-VANの仕様上、蓄積系JVOpenでは0B41は取得できず、速報系JVRTOpenで過去日付を指定する裏技的な方法になる)
            
            if data_spec == "0B41":
                # 日付リストを作成
                current = datetime.strptime(start_date, "%Y%m%d")
                end = datetime.strptime(end_date, "%Y%m%d")
                
                print(f"JVRTOpenによる日次取得モードを開始します (期間: {start_date}-{end_date})")
                
                while current <= end:
                    target_date = current.strftime("%Y%m%d")
                    print(f"\nProcessing Date: {target_date}...")
                    
                    # JVRTOpen (速報系)
                    # keyにYYYYMMDDを指定することで、過去の速報データを再生できる
                    res = self.jvlink.JVRTOpen(data_spec, target_date)
                    
                    if res == 0:
                        print(f"  [OK] データ取得開始 ({target_date})")
                        self._read_jvdata()
                        # JVRTOpenの場合はJVCloseが必要
                        self.jvlink.JVClose()
                    elif res == -1:
                        print(f"  [SKIP] データなし/終了 ({target_date})")
                    else:
                         print(f"  [ERROR] JVRTOpen失敗: {res}")
                         
                    current += timedelta(days=1)
                
                print("\n全日程の処理が完了しました")
                return

            # 以下は通常のJVOpen (RACEなど) の処理
            # JVOpen - データ読み込み開始
            # dataspec="RACE" はレース詳細情報
            # from_time は YYYYMMDDhhmmss 形式（14桁）が必須
            
            # data_spec は引数で指定されたものを使用
            # start_date は "YYYYMMDD" なので、後ろに "000000" を付加して14桁にする
            from_time = f"{start_date}000000"
            
            # option=1 (通常) は直近1年のみ。
            # 過去データ（1年以上前）を取得するには option=4 (セットアップ・ダイアログなし) が必要
            option = 4
            
            # JVOpenの戻り値
            # win32comでは (result_code, read_count, download_count, timestamp) のタプルが返る
            ret_tuple = self.jvlink.JVOpen(data_spec, from_time, option)
            
            # タプルから値を展開
            # 古いバージョンのwin32comや設定によっては単一の値が返る可能性もあるため型チェック
            if isinstance(ret_tuple, tuple):
                result = ret_tuple[0]
                read_count = ret_tuple[1]
                download_count = ret_tuple[2]
                timestamp = ret_tuple[3]
            else:
                result = ret_tuple
                read_count = 0
                download_count = 0
                timestamp = ""
            
            print(f"JVOpen結果コード: {result}")
            print(f"  詳細: {ret_tuple}")
            print(f"  dataspec={data_spec}, from_time={from_time}, option={option}")
            
            if result == 0:
                # データ読み込み処理
                print(f"  読み込みファイル数: {read_count}, ダウンロード数: {download_count}")
                self._read_jvdata()
            else:
                print(f"[WARNING] データ取得失敗: エラーコード {result}")
                if result == -112:
                     print("  → パラメータ不正 (JV_ERR_KEY? Dataspec?) キーの形式を確認してください")
                elif result == -201:
                    print("  → JVInitが正常に完了していません")
                elif result == -203:
                    print("  → 該当データが存在しません")
                
        except Exception as e:
            print(f"[ERROR] データ取得エラー: {e}")
        finally:
            if self.jvlink:
                try:
                    self.jvlink.JVClose()
                except:
                    pass
    
    def _read_jvdata(self):
        """JVDataからデータを読み込む"""
        print("\nデータ読み込み中...")
        record_count = 0
        parser = JVDataParser(DB_PATH)
        
        try:
            loop_count = 0
            while True:
                loop_count += 1
                # JVGetsを使用（JVReadは.NET環境でSEHExceptionの原因になる）
                # byte配列バッファを使用することで安全性を確保
                buff_size = 50000
                buff = bytearray(buff_size)  # byte配列バッファ
                filename = [""]
                record_spec = [""]
                
                # JVGets: ref object buff, int size を使用
                # Python(win32com)では、outパラメータ(filename)は戻り値として返されるため引数には含めない
                # 入力: buff, buff_size
                # 出力: (result_code, filename) のタプル（予想）
                
                # JVGets: ref object buff, int size を使用
                # Python(win32com)では、outパラメータ(buffも含む?)は戻り値として返される可能性がある
                
                # buff_sizeは毎回渡す
                # retは (result_code, returned_buffer, filename) の可能性がある
                ret = self.jvlink.JVGets(buff, buff_size)
                
                # 戻り値の型確認と展開
                if isinstance(ret, tuple):
                    # (result_code, returned_buffer, filename)
                    result = ret[0]
                    # バッファが戻り値に含まれている場合、そちらを使う
                    # ret[1] が memoryview や bytes の可能性がある
                    if len(ret) > 1:
                        data_blob = ret[1]
                        # memoryviewなどの場合、bytesに変換
                        try:
                            raw_data = bytes(data_blob)
                        except:
                            raw_data = bytes(buff[:result]) if result > 0 else b""
                    else:
                        raw_data = buff[:result]
                        
                    # filenameは3番目の要素
                    filename = ret[2] if len(ret) > 2 else ""
                else:
                    # 単一の値の場合（想定外だが）
                    result = ret
                    filename = ""
                    raw_data = buff[:result]
                
                if result == 0:
                    # 正常終了
                    break
                elif result == -1:
                    # ファイル切り替え
                    print(f"  ファイル切り替え: {filename}")
                    continue
                elif result > 0:
                    # データ取得成功
                    record_count += 1
                    
                    # raw_dataは恐らく全バッファサイズ分あるので、result長で切り取る必要があるかも？
                    # あるいはJVGetsが有効データ分だけ返しているか確認が必要
                    # 通常は buff[:result] だが、戻り値のblobがサイズ調整されているか不明
                    # 安全のためスライスする
                    current_data = raw_data[:result]
                    
                    # レコード種別はデータの先頭2バイト
                    try:
                        rec_type = current_data[:2].decode('ascii', errors='ignore')
                    except:
                        rec_type = "??"

                    # DEBUG: 生データの構造確認
                    if rec_type == "RA" or rec_type.startswith("O1"):
                        print(f"\n[{rec_type}] Record Found (Len={len(current_data)})")
                        print(f"Hex: {current_data[:100].hex()}")
                        # ASCIIでの表示（デバッグ用）
                        readable = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in current_data[:100]])
                        print(f"Str: {readable}")
                        
                        # 解析テスト
                        if rec_type == "RA":
                            # 試しに現在のオフセットでパースしてみる
                            try:
                                year = current_data[18:22].decode('ascii', errors='replace')
                                name = current_data[112:162].decode('shift_jis', errors='replace').strip()
                                print(f"Test Parse: Year={year}, Name={name}")
                            except Exception as e:
                                print(f"Test Parse Error: {e}")
                            
                            # RAとO1の両方が見つかるまで待ちたいが、とりあえずRAが見つかったら構造確認のため一旦停止でも良い
                            # いや、O1も見たい
                            pass

                    # レコードタイプに応じて処理
                    if rec_type == "RA":
                        parser.parse_race_record(current_data)
                    elif rec_type.startswith("O"):
                        parser.parse_odds_record(current_data, rec_type)
                        
                    # デバッグ用に最初の数件で止めるならここで回数制限
                    # if record_count > 5000: break
                    
                    if record_count % 100 == 0:
                        print(f"  処理済みレコード数: {record_count}")
                        parser.commit()  # 定期的にコミット
                else:
                    print(f"[WARNING] JVRead エラー: {result}")
                    break
                    
        except Exception as e:
            print(f"[ERROR] データ読み込みエラー: {e}")
        finally:
            parser.commit()
            parser.close()
        
        print(f"\n合計 {record_count} レコードを処理しました")
    
    def close(self):
        """接続を閉じる"""
        if self.conn:
            self.conn.close()
            print("データベース接続を閉じました")

def main():
    """メイン処理"""
    print("=" * 60)
    print("JV-Link データ取得ツール")
    print("=" * 60)
    
    # サービスキーは環境変数または設定ファイルから読み込む
    service_key = os.getenv("JRAVAN_SERVICE_KEY", "UNKNOWN")
    # キーの整形: 空白除去とハイフン除去
    service_key = service_key.strip().replace('-', '')
    
    collector = JVLinkCollector(service_key)
    
    if collector.connect():
        # ユーザーに取得期間を入力させる
        print("取得したい期間を入力してください (形式: YYYYMMDD)")
        
        # 開始日
        default_start = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
        start_date = input(f"開始日 [Enterで {default_start}]: ").strip()
        if not start_date:
            start_date = default_start
            
        # 終了日
        default_end = datetime.now().strftime("%Y%m%d")
        end_date = input(f"終了日 [Enterで {default_end}]: ").strip()
        if not end_date:
            end_date = default_end
            
        # データ種別の選択
        print("\n取得するデータの種類を選んでください:")
        print("  1: 確定オッズのみ (高速・推奨) - レース結果のオッズのみ取得")
        print("  2: 時系列オッズ (低速・大量) - 発売開始からのオッズ推移を取得（※JRA-VANにデータが残っている限り全て）")
        
        dtype_sel = input("選択 [Enterで 1]: ").strip()
        if dtype_sel == "2":
            data_spec = "0B41"  # 時系列オッズ
            print("→ 時系列オッズ (0B41) を取得します")
        else:
            data_spec = "RACE"  # 確定オッズ
            print("→ 確定オッズ (RACE) を取得します")
            
        print(f"確認: {start_date} から {end_date} までのデータを取得します...")
        
        collector.fetch_historical_odds(start_date, end_date, data_spec)
        
        collector.close()
    else:
        print("接続に失敗しました")

if __name__ == '__main__':
    main()
