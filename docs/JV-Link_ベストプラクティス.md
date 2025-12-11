# JV-Link 開発ベストプラクティス

## ⚠️ 重要: JVRead vs JVGets

### 結論: **必ずJVGetsを使用すること**

---

## 問題: JVReadの危険性

### C#/.NET環境での問題

```csharp
// ❌ 危険: JVReadは使用しない
JVRead(out string buff, int size, ...)
```

**問題点:**
- JVReadは「呼び出し側バッファ前提」のAPI
- .NET COMラッパーが生成するstring marshalingと整合しない
- **速報系（JVRTOpen）でSEHException（0x80010105）が発生**

### Python環境でも同様の問題

Pythonでも文字列バッファを使用すると、メモリ管理の不整合が発生する可能性があります。

---

## ✅ 解決策: JVGetsを使用

### 正しい実装（Python）

```python
# ✅ 安全: JVGetsを使用
buff_size = 50000
buff = bytearray(buff_size)  # byte配列バッファ
filename = [""]
record_spec = [""]

result = jvlink.JVGets(buff, buff_size, filename, record_spec)

if result > 0:
    # byte配列から文字列にデコード
    data = buff[:result].decode('shift_jis', errors='ignore')
```

### JVGetsの利点

1. **byte配列バッファを呼び出し側で保持**
   - JV-Link APIの設計と一致
   - メモリ管理が安全

2. **速報系（JVRTOpen）で安定**
   - rc=0でもクラッシュしない
   - データ不在時も安全に処理

3. **蓄積系（JVOpen）でも使用可能**
   - 速報・蓄積どちらも同じインターフェイス
   - コードの統一性が向上

---

## 🔍 速報系（JVRTOpen）の注意点

### rc=0 はデータ存在の保証ではない

```python
result = jvlink.JVGets(buff, buff_size, filename, record_spec)

if result == 0:
    # データなし、少し待機
    time.sleep(1)
    continue
elif result == -1:
    # ファイル切り替え
    continue
elif result > 0:
    # データ取得成功
    data = buff[:result].decode('shift_jis', errors='ignore')
```

**重要:**
- 実データが存在しないタイミングでは `rc=0` でも JVRead が暴走し得る
- **JVGetsは rc<=0 を安全に返す**ため、速報系では必須

---

## 📋 実装チェックリスト

### 蓄積系（JVOpen）

- [ ] JVGetsを使用
- [ ] byte配列バッファ（bytearray）を使用
- [ ] Shift_JISでデコード
- [ ] rc=0, rc=-1, rc>0 を適切に処理

### 速報系（JVRTOpen）

- [ ] **必ずJVGetsを使用**（JVReadは絶対に使わない）
- [ ] byte配列バッファ（bytearray）を使用
- [ ] rc=0 の場合は待機処理
- [ ] Shift_JISでデコード

---

## 🛠️ コード例

### 蓄積系データ取得

```python
def fetch_historical_data(self):
    """過去データ取得（蓄積系）"""
    # JVOpen実行後...
    
    while True:
        buff_size = 50000
        buff = bytearray(buff_size)
        filename = [""]
        record_spec = [""]
        
        result = self.jvlink.JVGets(buff, buff_size, filename, record_spec)
        
        if result == 0:
            break  # 正常終了
        elif result == -1:
            print(f"ファイル切り替え: {filename[0]}")
            continue
        elif result > 0:
            data = buff[:result].decode('shift_jis', errors='ignore')
            # データ処理...
```

### 速報系リアルタイム監視

```python
def realtime_monitor(self):
    """リアルタイム監視（速報系）"""
    # JVRTOpen実行後...
    
    while self.is_monitoring:
        buff_size = 50000
        buff = bytearray(buff_size)
        filename = [""]
        record_spec = [""]
        
        result = self.jvlink.JVGets(buff, buff_size, filename, record_spec)
        
        if result == 0:
            # データなし、待機
            time.sleep(1)
            continue
        elif result == -1:
            print(f"ファイル切り替え: {filename[0]}")
            continue
        elif result > 0:
            data = buff[:result].decode('shift_jis', errors='ignore')
            # データ処理...
```

---

## 📚 参考情報

### 文字エンコーディング

JV-Dataは **Shift_JIS** でエンコードされています。

```python
# デコード時のエラーハンドリング
data = buff[:result].decode('shift_jis', errors='ignore')
```

`errors='ignore'` により、不正な文字があっても処理を継続できます。

---

## ⚡ パフォーマンス

### バッファサイズ

```python
buff_size = 50000  # 推奨サイズ
```

- JV-Dataの最大レコード長に対応
- メモリ効率とパフォーマンスのバランス

---

**まとめ**: 蓄積系・速報系を問わず、**常にJVGetsを使用**することで、安定性と一貫性を確保できます。
