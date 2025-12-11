"""
現在のPython実装（問題あり）
"""

# ============================================================
# JVInit部分
# ============================================================

# collector.py の connect() メソッド

self.jvlink = win32com.client.Dispatch("JVDTLab.JVLink")

# サービスキーが空の場合、JV-Link設定ツールのキーを使用
if self.service_key:
    result = self.jvlink.JVInit(self.service_key)
else:
    # 引数なしで呼び出すと、設定ツールのキーが使われる
    result = self.jvlink.JVInit()

# 結果: JVInit結果: -103 （認証エラー）


# ============================================================
# JVOpen部分（過去データ取得）
# ============================================================

# collector.py の fetch_historical_odds() メソッド

# データ種別
data_spec = f"RACE{start_date}{end_date}"  # 例: "RACE2024060120240607"
from_time = start_date  # 例: "20240601"
option = 1  # 通常読み込み

# JVOpen実行
result = self.jvlink.JVOpen(data_spec, from_time, option)

# 結果: JVOpen結果: (-201, 0, 0, '') 
# -201 = JVInitが正常に完了していない


# ============================================================
# JVGets部分（データ読み込み）
# ============================================================

# collector.py の _read_jvdata() メソッド

buff_size = 50000
buff = bytearray(buff_size)  # byte配列バッファ
filename = [""]
record_spec = [""]

# JVGets でデータ取得
result = self.jvlink.JVGets(buff, buff_size, filename, record_spec)

if result == 0:
    # 正常終了
    break
elif result == -1:
    # ファイル切り替え
    continue
elif result > 0:
    # データ取得成功
    data = buff[:result].decode('shift_jis', errors='ignore')
    rec_type = record_spec[0]
    # パース処理...


# ============================================================
# 参考：C#で成功している実装
# ============================================================

"""
// JVInit
JVLinkClass jv = new JVLinkClass();
int rc = jv.JVInit("RtOddsTest");  // ← この文字列で成功
int status = jv.JVStatus();
Console.WriteLine($"[JVInit] rc={rc}, JVStatus={status}");

// JVRTOpen（速報系）
rc = jv.JVRTOpen("0B31", "202512070709");  // dataspec, raceId

// JVGets
byte[] buffer = new byte[110000];
object buffObj = buffer;
string fileName = "";
rc = jv.JVGets(ref buffObj, buffSize, out fileName);
"""


# ============================================================
# エラー状況
# ============================================================

"""
1. JVInit結果: -103
   - サービスキー認証エラー
   - jvlink_test.py では JVInit("UNKNOWN") で成功
   - collector.py では -103 エラー

2. JVOpen結果: (-201, 0, 0, '')
   - JVInitが正常に完了していない
   - JVInitが成功しないとJVOpenも失敗する

3. 試したこと
   - サービスキー: "1UJC-UWVR-4A0U-4XZS-4" → -103
   - サービスキー: "UNKNOWN" → -103
   - サービスキー: "RtOddsTest" → -103
   - サービスキー: 空文字列 → -103
   - 引数なし JVInit() → -103

4. 環境
   - Python 32bit版 (3.14.2)
   - JV-Link SDK Ver4.9.0.2 再インストール済み
   - jvlink_test.py では接続成功（JVInit成功）
"""


# ============================================================
# 質問
# ============================================================

"""
1. C#の JVInit("RtOddsTest") は実際のサービスキーではなく識別子？
2. JV-Link設定ツールにサービスキーを登録する必要がある？
3. JVOpen のパラメータ（data_spec, from_time, option）は正しい？
4. なぜ jvlink_test.py では成功するのに collector.py では失敗する？
"""
