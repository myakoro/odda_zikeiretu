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
        self.conn = None
        # DBパスを絶対パス化して、実行ディレクトリによる不一致を完全に防ぐ
        import os
        self.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "odds_history.db"))
        
        # 固定バッファを初期化(32bit環境での断片化対策)
        # 32KB に縮小。断片化に強く、ドライバの動作を最も安定させるサイズ。
        self._buff_size = 32768
        self._buff = bytearray(self._buff_size)
        
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
            
            
            # 既存の接続があれば閉じる
            if self.conn:
                try: self.conn.close()
                except: pass
            
            # データベース接続
            self.conn = sqlite3.connect(self.db_path, timeout=30)
            cur = self.conn.cursor()
            
            # 診断情報ログ
            db_list = cur.execute("PRAGMA database_list").fetchall()
            print(f"  [DB] 接続成功: {self.db_path}")
            print(f"  [DB] 物理ファイル: {db_list[0][2]}")
            
            # WALモードを有効化（書き込み性能向上、ロック競合軽減）
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.execute("PRAGMA cache_size=10000")
            print(f"[OK] データベース接続: {self.db_path}")
            
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
                    from datetime import datetime, timedelta
                    
                    # 完了済みレース管理用
                    CHECKPOINT_FILE = "data/completed_races.log"
                    ATTEMPT_FILE = "data/last_attempt.txt"
                    
                    completed_races = {}  # {race_id: fetch_date}
                    today = datetime.now().date()
                    
                    # 1. 完了済みリストの読み込み
                    if os.path.exists(CHECKPOINT_FILE):
                        try:
                            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                                for line in f:
                                    line = line.strip()
                                    if not line:
                                        continue
                                    
                                    # 新形式: race_id,date または 旧形式: race_id のみ
                                    if ',' in line:
                                        race_id, fetch_date_str = line.split(',', 1)
                                        try:
                                            fetch_date = datetime.strptime(fetch_date_str, "%Y-%m-%d").date()
                                            completed_races[race_id] = fetch_date
                                        except:
                                            # 日付パースエラー → 旧形式として扱う
                                            completed_races[race_id] = None
                                    else:
                                        # 旧形式（日付なし）
                                        completed_races[race_id] = None
                            
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
                                        f.write(f"{last_attempt_rk},{today.strftime('%Y-%m-%d')}\n")
                                    completed_races[last_attempt_rk] = today
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
                                f.write(f"{rk},{today.strftime('%Y-%m-%d')}\n")
                            completed_races[rk] = today
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
                        import gc
                        gc.collect() # 毎レース開始前に大掃除
                        
                        for attempt in range(max_retries):
                            try:
                                # 2回目以降は少し待つ
                                if attempt > 0:
                                    time.sleep(2.0)
                                    print(f"      -> リトライ中 ({attempt+1}/{max_retries})...")
                                    
                                # 常に初期化してから開始（安定性の究極対策）
                                if attempt >= 0:
                                    # print(f"      -> [Init] レース開始前のクリーンアップ...")
                                    try: 
                                        if self.jvlink: self.jvlink.JVClose()
                                    except: pass
                                    self.jvlink = None
                                    import gc
                                    gc.collect()
                                    
                                    if not self.connect():
                                         print("      -> [FATAL] 接続に失敗しました")
                                         return False
                                         
                                res_rt = self.jvlink.JVRTOpen("0B41", rk)
                                
                                if res_rt == 0:
                                    if self._read_jvdata():
                                        try: self.jvlink.JVClose()
                                        except: pass
                                        self.jvlink = None # 確実に捨てる
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

                            except BaseException as e_race:
                                import traceback
                                print(f"      -> [FATAL] レース処理中に例外発生: {repr(e_race)}")
                                traceback.print_exc()
                                try: self.jvlink.JVClose()
                                except: pass
                        
                        return False


                    # 2. 日付ごとにまとめて処理
                    sorted_dates = sorted(date_race_map.keys())
                    
                    # 定期的なドライバリセット用カウンター
                    processed_count = 0
                    race_interval_count = 0  # 24レース毎のインターバル用カウンター
                    
                    for d_str in sorted_dates:
                        keys = date_race_map[d_str]
                        
                        # 未完了のレースまたは30日以上前に取得したレースを対象とする
                        pending_keys = []
                        for k in keys:
                            if k not in completed_races:
                                # 未取得 → 対象
                                pending_keys.append(k)
                            else:
                                fetch_date = completed_races[k]
                                if fetch_date is None:
                                    # 旧形式（日付なし） → 再取得しない
                                    continue
                                
                                days_ago = (today - fetch_date).days
                                if days_ago >= 30:
                                    # 30日以上前 → 再取得対象
                                    pending_keys.append(k)
                                    print(f"  [Reacquire] {k} ({days_ago}日前に取得済み → 再取得)")
                        
                        if not pending_keys:
                            print(f"Skipping Date: {d_str} (All {len(keys)} races completed within 30 days)")
                            continue
                            
                        print(f"\nProcessing Date: {d_str} ({len(pending_keys)}/{len(keys)} races)...")
                        
                        for i, rk in enumerate(keys):
                            # 30日以内に取得済みならスキップ
                            if rk in completed_races:
                                fetch_date = completed_races[rk]
                                if fetch_date is not None:
                                    days_ago = (today - fetch_date).days
                                    if days_ago < 30:
                                        continue  # 30日以内 → スキップ
                                else:
                                    # 旧形式 → スキップ
                                    continue
                                
                            print(f"    - [{i+1}/{len(keys)}] Race {rk} 取得中...", end=" ", flush=True)
                            
                            # ★クラッシュ検知用に「今からこれやります」を書く
                            mark_attempt_start(rk)
                            
                            if process_race_with_retry(rk, max_retries=3):
                                # 成功したらチェックポイント保存 & 試行ファイル削除 (関数内で削除)
                                mark_race_complete(rk)
                                print("[OK]")
                                
                                # 成功カウントを増やす
                                processed_count += 1
                                
                                # 48レースごとに定期的なドライバリセット（最大の安定化処置）
                                if processed_count % 48 == 0:
                                    print(f"\n    [Maintenance] {processed_count}レース処理完了。ドライバをリフレッシュします...")
                                    try:
                                        self.jvlink.JVClose()
                                    except: pass
                                    self.jvlink = None
                                    gc.collect()
                                    time.sleep(10)  # ドライバ完全初期化のため10秒待機
                                    
                                    if not self.connect():
                                        print("    [ERROR] ドライバ再接続に失敗しました")
                                        return
                                    print("    [OK] ドライバリフレッシュ完了")
                                    
                            else:
                                print(f"[Failed] -> 3回失敗")
                                failed_races.append(rk)
                                # 失敗しても、とりあえず次に進むので試行ファイルは消していいかも？
                                # いや、失敗して落ちてないなら消すべき。
                                if os.path.exists(ATTEMPT_FILE):
                                    try: os.remove(ATTEMPT_FILE)
                                    except: pass
                            
                            # JRA-VANサーバー負荷軽減とライブラリ安定のため少し待機
                            time.sleep(0.6)
                            
                            # 12レース毎に5秒のインターバル + メモリ解放
                            race_interval_count += 1
                            if race_interval_count % 12 == 0:
                                print(f"\n    [Interval] {race_interval_count}レース処理完了。メモリ解放のため5秒待機します...")
                                gc.collect()  # 明示的にメモリ解放
                                time.sleep(5.0)
                                print("    [Interval] 再開します")
                    
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
                print("  [DEBUG] _read_jvdata 呼び出し直前...")
                self._read_jvdata()
                print("  [DEBUG] _read_jvdata 呼び出し完了")
            else:
                print(f"[WARNING] データ取得失敗: エラーコード {result}")
                if result == -112:
                     print("  → パラメータ不正 (JV_ERR_KEY? Dataspec?) キーの形式を確認してください")
                elif result == -201:
                    print("  → JVInitが正常に完了していません")
                elif result == -203:
                    print("  → 該当データが存在しません")
                
            print("  [DEBUG] fetch_historical_odds 正常終了処理中...")
            try: self.jvlink.JVClose()
            except: pass
            
        except BaseException as root_e:
            import traceback
            print("\n" + "!"*50)
            print(f"[CRITICAL FATAL] プログラムが予期せず終了しました:")
            print(f"種別: {type(root_e)}")
            print(f"内容: {repr(root_e)}")
            print("!"*50)
            traceback.print_exc()
            try: self.jvlink.JVClose()
            except: pass
        finally:
            if self.jvlink:
                try:
                    self.jvlink.JVClose()
                except:
                    pass
    
    def _read_jvdata(self):
        """JVDataからデータを読み込む. 成功ならTrue"""
        try:
            print(f"\n  [DEBUG] _read_jvdata 開始 (Thread ID: {hex(id(self))})")
            
            # parser側の接続を最新の状態にする
            self.parser = JVDataParser(self.db_path)
            self.parser.conn = self.conn
            self.parser.cursor = self.conn.cursor()
            
            records = 0
            success = True
            
            print(f"  [DEBUG] 読み込みループ開始 (BufferSize: {self._buff_size})")
            loop_count = 0
            # 最初の読み込み前に少し待機してドライバを安定させる
            import time
            time.sleep(0.5)
            
            while True:
                loop_count += 1
                # ドライバに一息つかせる（重要：これがないと11R等の大量データでハングアップする）
                if loop_count % 10 == 0:
                    time.sleep(0.01)

                try:
                    # 呼び出し直前にログ（ここから戻ってこないならドライバのフリーズ）
                    if loop_count < 10 or loop_count % 100 == 0:
                        print(f"      [DEBUG] JVGets 実行中... (Loop: {loop_count})")
                    
                    ret = self.jvlink.JVGets(self._buff, self._buff_size)
                    
                    if loop_count < 10 or loop_count % 100 == 0:
                        print(f"      [DEBUG] JVGets 帰還 (Code: {ret[0] if isinstance(ret, tuple) else ret})")
                except Exception as e_com:
                    print(f"  [FATAL] JVGets 呼び出し自体が失敗: {e_com}")
                    return False
                
                if isinstance(ret, tuple):
                    result = ret[0]
                    if len(ret) > 1:
                        data_blob = ret[1]
                        try: raw_data = bytes(data_blob)
                        except: raw_data = self._buff[:result] if result > 0 else b""
                    else:
                        raw_data = self._buff[:result]
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
                    current_data = self._buff[:result] # ここでコピーが発生するが、resultが小さいので安全
                    
                    try:
                        rec_type = current_data[:2].decode('ascii', errors='ignore')
                    except:
                        rec_type = "??"

                    if rec_type == "RA":
                        parser.parse_race_record(current_data)
                        parser.commit()  # レース情報は即座にコミット
                    elif rec_type.startswith("O"):
                        parser.parse_odds_record(current_data, rec_type)
                        # オッズレコードは100件ごとにコミット（バランス重視）
                        if record_count % 100 == 0:
                            parser.commit()
                            print(f"    - [Progress] {record_count} レコード処理中 (最新: {filename})")
                else:
                    print(f"[WARNING] JVRead エラー: {result}")
                    success = False
                    break
                    
        except Exception as e:
            import traceback
            print(f"[ERROR] データ読み込みエラー: {e}")
            traceback.print_exc()  # デバッグ用: 詳細なエラー情報を表示
            success = False
        finally:
            print(f"  [DEBUG] _read_jvdata 終了処理中 (Records: {record_count})")
            parser.commit()
            parser.close()
            import gc
            gc.collect() # 確保した一時メモリを即座に解放
        
        print(f"  [DEBUG] _read_jvdata 正常終了 (Total: {record_count} records)")
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
