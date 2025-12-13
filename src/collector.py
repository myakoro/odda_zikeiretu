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
            if data_spec == "0B41":
                # 時系列オッズ(0B41)の場合
                print(f"時系列オッズ(0B41)取得モード (期間: {start_date}-{end_date})")
                print("※ まず期間内の全開催レースIDを一括検索します (開催のない日は自動スキップ)")

                # 1. StartDateからRACEデータを連続読み込みし、EndDateまでの全レースキーをメモリに格納
                # {date_str: [key1, key2...]}
                date_race_map = {}
                
                try:
                    # JVOpen("RACE", start_date)
                    res = self.jvlink.JVOpen("RACE", start_date + "000000", 1)
                    if isinstance(res, tuple): res = res[0]
                    
                    if res != 0:
                        print(f"  [ERROR] レース情報へのアクセスに失敗しました (Code={res})")
                        return

                    buff = bytearray(100000)
                    print(f"  レース開催日をスキャン中...")
                    
                    scan_count = 0
                    while True:
                        ret = self.jvlink.JVGets(buff, 100000)
                        rc = ret[0] if isinstance(ret, tuple) else ret
                        
                        if rc == 0: break # End of Data
                        if rc == -1: continue
                        
                        if rc > 0:
                            if isinstance(ret, tuple) and len(ret) > 1 and ret[1] is not None: 
                                try:
                                    data = bytes(ret[1])[:rc]
                                except:
                                    data = buff[:rc]
                            else: 
                                data = buff[:rc]
                            
                            rec_type = data[:2].decode('ascii', errors='ignore')
                            if rec_type == "RA":
                                try:
                                    y = data[11:15].decode('ascii')
                                    m = data[15:17].decode('ascii')
                                    d = data[17:19].decode('ascii')
                                    r_date = f"{y}{m}{d}"
                                    
                                    # 終了判定
                                    if r_date > end_date:
                                        break
                                    
                                    # 開始判定（念のため）
                                    if r_date < start_date:
                                        continue
                                        
                                    j = data[19:21].decode('ascii')
                                    r = data[25:27].decode('ascii')
                                    r_key = f"{y}{m}{d}{j}{r}"
                                    
                                    if r_date not in date_race_map:
                                        date_race_map[r_date] = []
                                    date_race_map[r_date].append(r_key)
                                    
                                    scan_count += 1
                                    if scan_count % 100 == 0:
                                        print(f"    Scanning... {r_date} ({scan_count} races found)", end="\r")
                                except:
                                    pass
                    
                    self.jvlink.JVClose() # RACE connection close
                    print(f"  スキャン完了: 全{scan_count}レース ({len(date_race_map)}開催日) を発見しました")
                    
                    if not date_race_map:
                        print("  (指定期間内にレース開催が見つかりませんでした)")
                        return

                    # 2. 日付ごとにまとめて処理
                    import time
                    import os
                    import gc
                    
                    # 完了済みレース管理用
                    CHECKPOINT_FILE = "data/completed_races.log"
                    ATTEMPT_FILE = "data/last_attempt.txt"
                    
                    completed_races = set()
                    
                    # 1. 完了済みリストの読み込み
                    if os.path.exists(CHECKPOINT_FILE):
                        try:
                            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                                completed_races = set(line.strip() for line in f if line.strip())
                            print(f"  [Resume] 過去の完了履歴 {len(completed_races)} 件を読み込みました。")
                        except:
                            pass
                            
                    # 2. クラッシュ検知（前回、処理中に落ちたかどうか）
                    if os.path.exists(ATTEMPT_FILE):
                        try:
                            with open(ATTEMPT_FILE, "r", encoding="utf-8") as f:
                                last_attempt_rk = f.read().strip()
                            
                            if last_attempt_rk and last_attempt_rk not in completed_races:
                                print(f"\n" + "!"*60)
                                print(f"[CRASH DETECTED] 前回、レース {last_attempt_rk} の処理中に強制終了した可能性があります。")
                                print(f"このレースを「スキップ対象」として登録し、先へ進みます。")
                                print(f"!"*60 + "\n")
                                
                                # スキップリストに追加（完了扱いにする）
                                try:
                                    with open(CHECKPOINT_FILE, "a", encoding="utf-8") as f:
                                        f.write(f"{last_attempt_rk}\n")
                                    completed_races.add(last_attempt_rk)
                                except: pass
                                
                            # 試行ファイルを削除（検知済みのため）
                            try: os.remove(ATTEMPT_FILE)
                            except: pass
                        except:
                            pass

                    # 失敗したレースを記録するリスト
                    failed_races = []

                    def mark_race_complete(rk):
                        """レース完了を記録"""
                        try:
                            with open(CHECKPOINT_FILE, "a", encoding="utf-8") as f:
                                f.write(f"{rk}\n")
                            completed_races.add(rk)
                            # 成功したので試行ファイルを削除
                            if os.path.exists(ATTEMPT_FILE):
                                try: os.remove(ATTEMPT_FILE)
                                except: pass
                        except:
                            pass
                            
                    def mark_attempt_start(rk):
                        """処理開始を記録（クラッシュ検知用）"""
                        try:
                            with open(ATTEMPT_FILE, "w", encoding="utf-8") as f:
                                f.write(str(rk))
                        except:
                            pass

                    def process_race_with_retry(rk, max_retries=3):
                        """指定したレースをリトライ付きで処理する. 成功ならTrue"""
                        for attempt in range(max_retries):
                            try:
                                # 2回目以降は少し待つ
                                if attempt > 0:
                                    time.sleep(2.0)
                                    print(f"      -> リトライ中 ({attempt+1}/{max_retries})...")
                                    
                                    # ★重要: リトライ時はJVLinkを再初期化する（不安定状態の解消）
                                    print("      -> [Re-Init] 接続を再確立しています...")
                                    try:
                                        self.jvlink.JVClose()
                                    except: pass
                                    self.jvlink = None
                                    gc.collect()
                                    
                                    # 再接続
                                    if not self.connect():
                                         print("      -> [FATAL] 再接続に失敗しました")
                                         return False
                                         
                                res_rt = self.jvlink.JVRTOpen("0B41", rk)
                                
                                if res_rt == 0:
                                    if self._read_jvdata():
                                        self.jvlink.JVClose()
                                        return True
                                    else:
                                        print(f"      -> 読み込みエラー。リトライします。")
                                        self.jvlink.JVClose()
                                else:
                                    # エラーコードを表示
                                    print(f"      -> JVRTOpen失敗 (Code={res_rt})")
                                    self.jvlink.JVClose() 
                                    
                                    # データ無し(-203)や除外(-111)、汎用エラー(-1)の場合はリトライしても無駄なので即終了
                                    if res_rt == -203 or res_rt == -111 or res_rt == -1:
                                        print("      -> [SKIP] データが存在しないか、取得できません (Code=-1/-111/-203)。")
                                        return False

                            except Exception as e:
                                print(f"      -> [ERROR] 例外発生: {repr(e)}")
                                try: self.jvlink.JVClose()
                                except: pass
                            except Exception as e:
                                print(f"      -> [ERROR] 例外発生: {repr(e)}")
                                try: self.jvlink.JVClose()
                                except: pass
                        
                        return False


                    # 2. 日付ごとにまとめて処理
                    sorted_dates = sorted(date_race_map.keys())
                    
                    for d_str in sorted_dates:
                        keys = date_race_map[d_str]
                        
                        # 未完了のレースがあるか確認
                        pending_keys = [k for k in keys if k not in completed_races]
                        
                        if not pending_keys:
                            print(f"Skipping Date: {d_str} (All {len(keys)} races completed)")
                            continue
                            
                        print(f"\nProcessing Date: {d_str} ({len(pending_keys)}/{len(keys)} races)...")
                        
                        for i, rk in enumerate(keys):
                            if rk in completed_races:
                                continue
                                
                            print(f"    - [{i+1}/{len(keys)}] Race {rk} 取得中...", end=" ", flush=True)
                            
                            # ★クラッシュ検知用に「今からこれやります」を書く
                            mark_attempt_start(rk)
                            
                            if process_race_with_retry(rk, max_retries=3):
                                # 成功したらチェックポイント保存 & 試行ファイル削除 (関数内で削除)
                                mark_race_complete(rk)
                                print("[OK]")
                            else:
                                print(f"[Failed] -> 3回失敗")
                                failed_races.append(rk)
                                # 失敗しても、とりあえず次に進むので試行ファイルは消していいかも？
                                # いや、失敗して落ちてないなら消すべき。
                                if os.path.exists(ATTEMPT_FILE):
                                    try: os.remove(ATTEMPT_FILE)
                                    except: pass
                            
                            # JRA-VANサーバー負荷軽減とライブラリ安定のため少し待機
                            time.sleep(0.1)
                    
                    # 3. 取得できなかったデータの再取得試行
                    if failed_races:
                        print(f"\n" + "="*50)
                        print(f"取得失敗したレースが {len(failed_races)} 件あります。")
                        print(f"再取得を試みます...")
                        print(f"="*50)
                        
                        permanently_failed = []
                        
                        for i, rk in enumerate(failed_races):
                            print(f"    - [再試行 {i+1}/{len(failed_races)}] Race {rk}...")
                            if not process_race_with_retry(rk, max_retries=3):
                                print(f"      -> [完全失敗] データが取得できませんでした。")
                                permanently_failed.append(rk)
                            else:
                                print(f"      -> [リカバリ成功]")
                            time.sleep(0.5) # リトライ時は長めに待機
                        
                        if permanently_failed:
                            print(f"\n" + "!"*50)
                            print(f"[報告] 以下のレースはデータが存在しないか、取得できませんでした:")
                            for rk in permanently_failed:
                                print(f"  - {rk}")
                            print(f"!"*50)
                        else:
                            print(f"\n[報告] 全ての失敗データのリカバリに成功しました！")
                                
                except Exception as e:
                     import traceback
                     print(f"  [ERROR] 初期化/スキャンエラー: {e}")
                     traceback.print_exc()
                     try: self.jvlink.JVClose() 
                     except: pass
                
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
            import traceback
            print(f"[ERROR] データ取得エラー: {e}")
            traceback.print_exc()
        finally:
            if self.jvlink:
                try:
                    self.jvlink.JVClose()
                except:
                    pass
    
    def _read_jvdata(self):
        """JVDataからデータを読み込む. 成功ならTrue"""
        print("\nデータ読み込み中...")
        record_count = 0
        parser = JVDataParser(DB_PATH)
        success = True
        
        try:
            loop_count = 0
            while True:
                loop_count += 1
                buff_size = 40000 # バッファサイズを標準的に戻す（安定重視）
                buff = bytearray(buff_size)
                
                ret = self.jvlink.JVGets(buff, buff_size)
                
                if isinstance(ret, tuple):
                    result = ret[0]
                    if len(ret) > 1:
                        data_blob = ret[1]
                        try: raw_data = bytes(data_blob)
                        except: raw_data = buff[:result] if result > 0 else b""
                    else:
                        raw_data = buff[:result]
                    filename = ret[2] if len(ret) > 2 else ""
                else:
                    result = ret
                    filename = ""
                    raw_data = buff[:result]
                
                if result == 0:
                    break
                elif result == -1:
                    print(f"  ファイル切り替え: {filename}")
                    continue
                elif result > 0:
                    record_count += 1
                    current_data = raw_data[:result]
                    
                    try:
                        rec_type = current_data[:2].decode('ascii', errors='ignore')
                    except:
                        rec_type = "??"

                    if rec_type == "RA":
                        parser.parse_race_record(current_data)
                    elif rec_type.startswith("O"):
                        parser.parse_odds_record(current_data, rec_type)
                        
                    if record_count % 500 == 0:
                         parser.commit()
                else:
                    print(f"[WARNING] JVRead エラー: {result}")
                    success = False
                    break
                    
        except Exception as e:
            import traceback
            print(f"[ERROR] データ読み込みエラー: {e}")
            # traceback.print_exc()
            success = False
        finally:
            parser.commit()
            parser.close()
        
        print(f"\n合計 {record_count} レコードを処理しました")
        return success
    
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
            data_spec = "0B41"  # 時系列オッズ (標準)
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
