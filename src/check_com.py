"""
インストール済みのJV-Link COMオブジェクトを検索するスクリプト
"""
import winreg

def find_jvlink_progids():
    """レジストリからJV-Link関連のProgIDを検索"""
    print("=" * 60)
    print("JV-Link COM ProgID 検索")
    print("=" * 60)
    
    found_progids = []
    
    try:
        # HKEY_CLASSES_ROOT を検索
        root_key = winreg.HKEY_CLASSES_ROOT
        
        # JV関連のキーを探す
        search_terms = ["JV", "JRA", "DataLab"]
        
        print("\nレジストリを検索中...\n")
        
        i = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(root_key, i)
                
                # JV関連のキーをチェック
                for term in search_terms:
                    if term.lower() in subkey_name.lower():
                        try:
                            # CLSIDが存在するか確認
                            key_path = f"{subkey_name}\\CLSID"
                            key = winreg.OpenKey(root_key, key_path)
                            winreg.CloseKey(key)
                            
                            found_progids.append(subkey_name)
                            print(f"✓ 発見: {subkey_name}")
                        except:
                            pass
                
                i += 1
            except OSError:
                break
        
        if found_progids:
            print(f"\n合計 {len(found_progids)} 個のJV関連COMオブジェクトを発見しました")
            print("\n推奨される接続方法:")
            for progid in found_progids:
                print(f'  jvlink = win32com.client.Dispatch("{progid}")')
        else:
            print("\n⚠ JV関連のCOMオブジェクトが見つかりませんでした")
            print("\n考えられる原因:")
            print("  1. JV-Linkが正しくインストールされていない")
            print("  2. 32bit版Pythonが必要な可能性がある")
            print("  3. インストール後に再起動が必要な可能性がある")
        
    except Exception as e:
        print(f"✗ エラー: {e}")
    
    return found_progids

def test_progids(progids):
    """見つかったProgIDで接続テスト"""
    if not progids:
        return
    
    print("\n" + "=" * 60)
    print("接続テスト")
    print("=" * 60)
    
    import win32com.client
    
    for progid in progids:
        print(f"\n{progid} で接続テスト中...")
        try:
            obj = win32com.client.Dispatch(progid)
            print(f"  ✓ 接続成功！")
            
            # メソッド一覧を表示
            try:
                methods = [m for m in dir(obj) if not m.startswith('_')]
                print(f"  利用可能なメソッド: {', '.join(methods[:10])}...")
            except:
                pass
            
        except Exception as e:
            print(f"  ✗ 接続失敗: {e}")

if __name__ == '__main__':
    progids = find_jvlink_progids()
    test_progids(progids)
