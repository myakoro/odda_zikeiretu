# 投資競馬 時系列オッズ取得アプリ

JRA-VAN Data Lab SDK (JV-Link) を使用して、過去の時系列オッズデータおよびリアルタイムオッズを取得・蓄積・分析するシステムです。

## 📋 機能

- ✅ **過去データ取得**: JV-Linkから指定期間のレース情報とオッズデータを取得
- ✅ **ターゲットCSVインポート**: ターゲットからエクスポートした時系列オッズCSVをインポート（1年以上前のデータ取得に対応）
- ✅ **リアルタイム監視**: オッズ変動をリアルタイムで監視・記録
- ✅ **データベース保存**: SQLiteにレース情報とオッズ履歴を保存
- ✅ **Webダッシュボード**: モダンなUIでデータを可視化・分析
- ✅ **CSVエクスポート**: 蓄積データをCSV形式でエクスポート

## 🗂️ プロジェクト構成

```
時系列オッズ取得アプリ/
├── src/                    # Pythonソースコード
│   ├── init_db.py         # データベース初期化
│   ├── parser.py          # JV-Dataパーサー
│   ├── collector.py       # 過去データ取得
│   ├── import_from_target.py # ターゲットCSVインポート
│   ├── realtime_monitor.py # リアルタイム監視
│   ├── jvlink_test.py     # JV-Link接続テスト
│   └── api_server.py      # Flask APIサーバー
├── web/                    # Webダッシュボード
│   ├── index.html         # メインHTML
│   ├── styles.css         # スタイルシート
│   └── app.js             # JavaScript
├── data/                   # データベース保存先
│   └── odds_history.db    # SQLiteデータベース
├── target系/               # ターゲットCSVファイル保存先
├── docs/                   # ドキュメント
└── JRA-VAN Data Lab. SDK Ver4.9.0.2/  # SDK
```

## 🚀 セットアップ

### 1. 必要な環境

- **Windows OS** (JV-LinkはWindows専用)
- **Python 3.8以上 (32bit版)** ⚠️ 重要: JV-Linkは32bit ActiveXのため、**必ず32bit版Pythonを使用**
- JRA-VANの契約アカウント（データ取得に必要）

### 2. Python 32bit版のインストール

JV-Link ActiveXコントロールは32bit版のため、Python 64bitからは使用できません。

1. [Python公式サイト](https://www.python.org/downloads/)から**32bit版**をダウンロード
2. インストール時に「Add Python to PATH」にチェック
3. インストール先を確認（例: `C:\Python314-32`）

### 3. 仮想環境の作成（32bit）

```powershell
# プロジェクトディレクトリに移動
cd "C:\Users\takuy\Desktop\投資競馬アプリ系\時系列オッズ取得アプリ"

# 32bit Pythonで仮想環境を作成
C:\Python314-32\python.exe -m venv .venv32

# 仮想環境をアクティベート
.venv32\Scripts\Activate.ps1
```

### 4. 依存ライブラリのインストール

```powershell
pip install pywin32 pandas flask flask-cors
```

### 5. JV-Link SDKのインストール

```powershell
# SDKインストーラーを管理者権限で実行
Start-Process "JRA-VAN Data Lab. SDK Ver4.9.0.2\JV-Link\JV-Link.exe" -Verb RunAs
```

⚠️ **重要**: 本システムは**JVGets**を使用しています（JVReadは使用していません）
- JVReadは.NET環境でSEHException（0x80010105）を引き起こす可能性があります
- JVGetsはbyte配列バッファを使用し、速報系・蓄積系どちらでも安全に動作します
- 詳細は [`docs/JV-Link_ベストプラクティス.md`](docs/JV-Link_ベストプラクティス.md) を参照

### 6. データベース初期化

```powershell
python src/init_db.py
```

## 📖 使い方

### JV-Link接続テスト

```powershell
python src/jvlink_test.py
```

### 過去データ取得

```powershell
# collector.pyを編集してサービスキーを設定
python src/collector.py
```

### ターゲットCSVインポート（1年以上前のデータ）

JV-Link APIでは1年以上前のデータが取得できないため、ターゲットからエクスポートしたCSVをインポートできます。

```powershell
# 単一ファイルをインポート
python src/import_from_target.py target系/JD07255101.CSV

# 複数ファイルを一括インポート
python src/import_from_target.py "target系/*.CSV"
```

詳細は [`docs/ターゲットCSVインポート.md`](docs/ターゲットCSVインポート.md) を参照してください。

### リアルタイムオッズ監視

```powershell
python src/realtime_monitor.py
```

### Webダッシュボード起動

```powershell
python src/api_server.py
```

ブラウザで `http://localhost:5000` にアクセス

## 🎨 Webダッシュボード機能

1. **ダッシュボード**: 統計情報とリアルタイムオッズ推移グラフ
2. **レース一覧**: 日付・競馬場でレースを検索
3. **オッズ分析**: レースIDを指定してオッズ変動を分析
4. **設定**: データ取得・監視の設定、CSVエクスポート

## 🔑 サービスキーの設定

JRA-VANの契約キーを環境変数に設定することを推奨:

```powershell
$env:JRAVAN_SERVICE_KEY = "あなたのサービスキー"
```

または、各スクリプト内で直接指定してください。

## 📊 データベーススキーマ

### races テーブル
- `race_id`: レースID (主キー)
- `date`: 開催日
- `ba_code`: 競馬場コード
- `race_no`: レース番号
- `race_name`: レース名
- `start_time`: 発走時刻

### odds_history テーブル
- `id`: 自動採番ID (主キー)
- `race_id`: レースID (外部キー)
- `time_stamp`: 取得時刻
- `umaban`: 馬番
- `odds_tan`: 単勝オッズ
- `odds_fuku_min`: 複勝オッズ下限
- `odds_fuku_max`: 複勝オッズ上限
- `popularity`: 人気順

## ⚠️ 注意事項

- JV-Link SDKの使用にはJRA-VANの契約が必要です
- データ取得量によっては通信料金が発生する場合があります
- 本システムは投資を保証するものではありません

## 📝 ライセンス

個人利用のみ。JRA-VANの利用規約を遵守してください。
