# JV-Link 32bit/64bit 問題 - 解決ガイド

## 問題の概要

JRA-VAN Data Lab SDK (JV-Link) のActiveXコントロールは**32bit版**です。
現在使用中のPython 64bit版からは32bit COMコンポーネントにアクセスできないため、以下のエラーが発生します：

```
(-2147221164, 'クラスが登録されていません', None, None)
```

---

## 🎯 推奨解決策: Python 32bit版を使用

### ステップ1: Python 32bit版のインストール

1. [Python公式サイト](https://www.python.org/downloads/)にアクセス
2. 「Windows installer (32-bit)」をダウンロード
3. インストール時のオプション:
   - ✅ "Add Python to PATH" にチェック
   - インストール先: `C:\Python314-32` など（64bit版と区別）

### ステップ2: 32bit版仮想環境の作成

```powershell
# 時系列オッズ取得アプリのディレクトリに移動
cd "C:\Users\takuy\Desktop\投資競馬アプリ系\時系列オッズ取得アプリ"

# 32bit Python で仮想環境を作成
C:\Python314-32\python.exe -m venv .venv32

# 仮想環境をアクティベート
.venv32\Scripts\Activate.ps1
```

### ステップ3: 依存ライブラリのインストール

```powershell
# 仮想環境内で実行
pip install pywin32 pandas flask flask-cors
```

### ステップ4: JV-Link接続テスト

```powershell
python src/jvlink_test.py
```

成功すると以下のように表示されます：
```
✓ JV-Linkオブジェクトの作成に成功しました
✓ JVInit成功
```

---

## 🔍 確認方法

### 現在のPythonのビット数を確認

```powershell
python -c "import platform; print(f'Python: {platform.architecture()[0]}')"
```

- `64bit` → 64bit版（JV-Linkは使用不可）
- `32bit` → 32bit版（JV-Link使用可能）

---

## 📝 今後の開発フロー

### 1. 常に32bit仮想環境を使用

```powershell
# プロジェクトディレクトリで実行
.venv32\Scripts\Activate.ps1
```

### 2. スクリプト実行

```powershell
# データベース初期化
python src/init_db.py

# JV-Link接続テスト
python src/jvlink_test.py

# 過去データ取得
python src/collector.py

# リアルタイム監視
python src/realtime_monitor.py

# Webダッシュボード起動
python src/api_server.py
```

---

## 🛠️ 代替案（高度）

### 方法2: COMサロゲートプロセス

64bit Pythonから32bit COMを呼び出すための中間プロセスを作成します。

**メリット**: 64bit Pythonを継続使用可能
**デメリット**: 実装が複雑

### 方法3: VB.NETラッパー

VB.NETでJV-Link呼び出しプログラムを作成し、Pythonからサブプロセスとして実行します。

**メリット**: Pythonのビット数に依存しない
**デメリット**: VB.NET開発環境が必要

---

## ✅ チェックリスト

- [ ] Python 32bit版をインストール
- [ ] 32bit仮想環境を作成 (`.venv32`)
- [ ] 依存ライブラリをインストール
- [ ] JV-Link接続テストが成功
- [ ] JRA-VANサービスキーを設定
- [ ] データ取得・監視スクリプトを実行

---

**重要**: JV-Linkを使用する場合は、必ず**Python 32bit版**を使用してください。
