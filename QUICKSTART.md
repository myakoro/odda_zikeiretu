# クイックスタートガイド

## 🚀 すぐに始める（5分で動作確認）

### ステップ1: Webダッシュボードを起動

JV-Link接続なしでも、Webダッシュボードは動作します。

```powershell
# プロジェクトディレクトリに移動
cd "C:\Users\takuy\Desktop\投資競馬アプリ系\時系列オッズ取得アプリ"

# APIサーバーを起動
python src/api_server.py
```

ブラウザで以下にアクセス:
```
http://localhost:5000
```

### ステップ2: UIを確認

ダッシュボードで以下を確認できます:
- 📊 統計情報（レース数、オッズ記録数）
- 📅 レース一覧（日付・競馬場で検索）
- 📈 オッズ分析（時系列変動）
- ⚙️ 設定（データ取得・監視制御）

---

## 🔧 JV-Link接続（実データ取得）

### 前提条件

1. ✅ JRA-VANの契約アカウント
2. ✅ Python 32bit版のインストール
3. ✅ JV-Link SDKのインストール

### Python 32bit版のセットアップ

#### 1. Python 32bit版をダウンロード

[Python公式サイト](https://www.python.org/downloads/) → 「Windows installer (32-bit)」

#### 2. 仮想環境を作成

```powershell
# 32bit Pythonで仮想環境を作成
C:\Python314-32\python.exe -m venv .venv32

# アクティベート
.venv32\Scripts\Activate.ps1

# 確認（32bitと表示されればOK）
python -c "import platform; print(platform.architecture()[0])"
```

#### 3. 依存ライブラリをインストール

```powershell
pip install pywin32 pandas flask flask-cors
```

### JV-Link接続テスト

```powershell
python src/jvlink_test.py
```

**成功例:**
```
✓ JV-Linkオブジェクトの作成に成功しました
✓ JVInit成功
```

**失敗例（Python 64bitの場合）:**
```
✗ エラー: (-2147221164, 'クラスが登録されていません', None, None)
```
→ Python 32bit版を使用してください

---

## 📊 データ取得の流れ

### 1. サービスキーを設定

```powershell
# 環境変数に設定（推奨）
$env:JRAVAN_SERVICE_KEY = "あなたのサービスキー"
```

または、スクリプト内で直接指定:
```python
service_key = "あなたのサービスキー"
collector = JVLinkCollector(service_key)
```

### 2. 過去データを取得

```powershell
python src/collector.py
```

デフォルトでは過去7日分のデータを取得します。

### 3. リアルタイム監視を開始

```powershell
python src/realtime_monitor.py
```

オッズ更新をリアルタイムで監視し、データベースに保存します。

### 4. Webダッシュボードで分析

```powershell
python src/api_server.py
```

`http://localhost:5000` でデータを可視化・分析できます。

---

## 🎯 よくある質問

### Q1: JV-Linkに接続できません

**A:** Python 32bit版を使用していますか？

```powershell
python -c "import platform; print(platform.architecture()[0])"
```

`64bit` と表示される場合は、32bit版の仮想環境を作成してください。

### Q2: データが取得できません

**A:** JRA-VANのサービスキーを設定していますか？

```powershell
# 環境変数を確認
echo $env:JRAVAN_SERVICE_KEY
```

### Q3: Webダッシュボードにデータが表示されません

**A:** データベースにデータが存在しますか？

```powershell
# データベースを確認
python -c "import sqlite3; conn = sqlite3.connect('data/odds_history.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM races'); print(f'レース数: {cursor.fetchone()[0]}'); conn.close()"
```

---

## 📚 詳細ドキュメント

- [README.md](README.md) - 完全なセットアップガイド
- [docs/JV-Link_32bit_64bit問題.md](docs/JV-Link_32bit_64bit問題.md) - Python 32bit/64bit問題の詳細
- [docs/JV-Link_ベストプラクティス.md](docs/JV-Link_ベストプラクティス.md) - JVGets vs JVReadの解説

---

## 🆘 トラブルシューティング

| 問題 | 解決策 |
|------|--------|
| COMエラー (-2147221164) | Python 32bit版を使用 |
| JVInit失敗 (-1) | サービスキーを設定 |
| データなし | collector.pyを実行してデータ取得 |
| ポート5000が使用中 | api_server.pyのポート番号を変更 |

---

**今すぐ試す**: `python src/api_server.py` を実行して、Webダッシュボードを確認しましょう！
