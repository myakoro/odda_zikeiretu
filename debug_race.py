import win32com.client
import sys
import os

def check_race(target_date, target_key):
    print(f"Checking Race: Date={target_date}, Key={target_key}")
    
    try:
        jv = win32com.client.Dispatch("JRAVAN.JVLink")
        jv.JVInit("UNKNOWN")
        
        # 1. Check RA Record
        print(f"Reading RA record for date {target_date}...")
        try:
            res = jv.JVOpen("RACE", target_date + "000000", 1)
            if isinstance(res, tuple): res = res[0]
            print(f"JVOpen(RACE) Result: {res}")
            
            found = False
            full_hex = ""
            
            buff = bytearray(100000)
            while True:
                ret = jv.JVGets(buff, 100000)
                rc = ret[0] if isinstance(ret, tuple) else ret
                
                if rc == 0: break
                if rc > 0:
                    data = bytes(ret[1])[:rc] if len(ret) > 1 and ret[1] else buff[:rc]
                    rec_type = data[:2].decode('ascii', errors='ignore')
                    
                    if rec_type == "RA":
                        y = data[11:15].decode('ascii')
                        m = data[15:17].decode('ascii')
                        d = data[17:19].decode('ascii')
                        j = data[19:21].decode('ascii')
                        r = data[25:27].decode('ascii')
                        
                        r_key = f"{y}{m}{d}{j}{r}"
                        
                        if r_key == target_key:
                            print(f"Found RA Record for {r_key}")
                            print(f"  DataKubun (Offset 2): {chr(data[2])}")
                            print(f"  RaceName: {data[33:63].decode('shift_jis', errors='ignore').strip()}")
                            # Inspect potential status flags
                            # Offset 63 is GradeCD? 
                            found = True
                            full_hex = data.hex()
                            break
            jv.JVClose()
            
            if not found:
                print("RA record NOT found in scan.")
            
        except Exception as e:
            print(f"Scan Exception: {e}")
            
        # 2. Test JVRTOpen
        print(f"\nTesting JVRTOpen for {target_key}...")
        try:
            res = jv.JVRTOpen("0B41", target_key)
            print(f"JVRTOpen Result: {res}")
            jv.JVClose()
        except Exception as e:
            print(f"JVRTOpen Exception: {e}")

    except Exception as e:
        print(f"Main Exception: {e}")

if __name__ == "__main__":
    # Test typical failure case
    check_race("20250208", "202502080804")
