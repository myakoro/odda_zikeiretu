"""
JV-Link 接続テスト (複数のProgIDを試行)
"""
import win32com.client
import sys

def test_multiple_progids():
    """複数の可能性のあるProgIDで接続を試行"""
    print("=" * 60)
    print("JV-Link 接続テスト (複数ProgID試行)")
    print("=" * 60)
    
    # 試行するProgIDのリスト
    progids = [
        "JVDTLabLib.JVLink",
        "JVDTLab.JVLink",
        "JVLink.JVLink",
        "JRA.JVLink",
        "JRAVAN.JVLink",
    ]
    
    for progid in progids:
        print(f"\n{progid} で接続テスト中...")
        try:
            jvlink = win32com.client.Dispatch(progid)
            print(f"  ✓ 接続成功！")
            
            # JVInitを試行
            try:
                result = jvlink.JVInit("UNKNOWN")
                print(f"  ✓ JVInit実行成功 (結果: {result})")
                
                # バージョン取得を試行
                try:
                    version = jvlink.JVGetVersion()
                    print(f"  ✓ バージョン: {version}")
                except Exception as e:
                    print(f"  - バージョン取得: {e}")
                
                print(f"\n✅ 成功！使用するProgID: {progid}")
                return jvlink, progid
                
            except Exception as e:
                print(f"  ✗ JVInit失敗: {e}")
                
        except Exception as e:
            print(f"  ✗ 接続失敗: {e}")
    
    print("\n❌ すべてのProgIDで接続に失敗しました")
    return None, None

if __name__ == '__main__':
    jvlink, progid = test_multiple_progids()
    
    if jvlink:
        print("\n" + "=" * 60)
        print("推奨設定")
        print("=" * 60)
        print(f'jvlink = win32com.client.Dispatch("{progid}")')
    else:
        print("\n" + "=" * 60)
        print("トラブルシューティング")
        print("=" * 60)
        print("1. JV-Linkが正しくインストールされているか確認")
        print("2. 32bit版Pythonの使用を検討")
        print("   - JV-LinkのActiveXコントロールは32bit版の可能性があります")
        print("3. Windowsの再起動")
        sys.exit(1)
