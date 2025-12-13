import win32com.client
import os
from dotenv import load_dotenv

load_dotenv()

def check_2025():
    key = os.getenv("JRAVAN_SERVICE_KEY").strip().replace('-', '')
    jv = win32com.client.Dispatch("JVDTLab.JVLink")
    jv.JVInit(key)
    
    # 2025/01/05 (Sunday) - Should have races
    target = "20250105"
    
    for spec in ["0B12", "0B15", "0B42", "0B30"]:
        print(f"\nChecking {target} for {spec} (JVRTOpen)...")
        try:
            res = jv.JVRTOpen(spec, target)
            print(f"Result: {res}")
            
            if res == 0:
                print("Success! Data exists. Reading records...")
                buff = bytearray(100000)
                count = 0
                while True:
                    ret = jv.JVGets(buff, 100000)
                    if isinstance(ret, tuple):
                        rc = ret[0]
                        if rc > 0:
                            count += 1
                            if count <= 3:
                                data = buff[:rc]
                                rec_type = data[:2].decode('ascii', errors='ignore')
                                print(f"  Record {count}: Type={rec_type}, Len={rc}")
                        elif rc == 0:
                            break
                        elif rc == -1:
                            pass # file switch
                    else:
                        break
                    if count > 5: break
                print(f"Total read check: {count} records found (first few)")
                
            jv.JVClose()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_2025()
