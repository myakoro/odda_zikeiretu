"""
JV-Link 接続テストスクリプト
JRA-VAN Data Lab SDK (JV-Link) への接続を確認する
"""
import win32com.client
import sys

def test_jvlink_connection():
    """JV-Linkへの接続テスト"""
    try:
        print("JV-Linkオブジェクトを作成中...")
        jvlink = win32com.client.Dispatch("JVDTLab.JVLink")
        print("✓ JV-Linkオブジェクトの作成に成功しました")
        
        # JVInit - 初期化
        print("\nJVInitを実行中...")
        sid = "UNKNOWN"  # サービスキーは実際の契約キーに置き換える必要があります
        result = jvlink.JVInit(sid)
        
        if result == 0:
            print("[OK] JVInit成功")
        elif result == -1:
            print("[WARNING] JVInit: サービスキーが設定されていません")
            print("  → JRA-VANの契約キーを設定してください")
        else:
            print(f"[ERROR] JVInit結果コード: {result}")
        
        # バージョン情報取得
        try:
            version = jvlink.JVGetVersion()
            print(f"\nJV-Linkバージョン: {version}")
        except Exception as e:
            print(f"バージョン取得エラー: {e}")
        
        return jvlink
        
    except Exception as e:
        print(f"[ERROR] エラーが発生しました: {e}")
        print("\n考えられる原因:")
        print("  1. JRA-VAN Data Lab SDKがインストールされていない")
        print("  2. COMコンポーネントが正しく登録されていない")
        return None

if __name__ == '__main__':
    print("=" * 60)
    print("JV-Link 接続テスト")
    print("=" * 60)
    jvlink = test_jvlink_connection()
    
    if jvlink:
        print("\n接続テスト完了")
    else:
        print("\n接続テスト失敗")
        sys.exit(1)
