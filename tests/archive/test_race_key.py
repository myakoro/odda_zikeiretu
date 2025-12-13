import win32com.client
import os
from dotenv import load_dotenv

load_dotenv()

def check_race_access():
    key = os.getenv("JRAVAN_SERVICE_KEY").strip().replace('-', '')
    jv = win32com.client.Dispatch("JVDTLab.JVLink")
    jv.JVInit(key)
    
    # 1. Get a valid Race Key for 2025/01/05
    target_date = "20250105000000"
    print(f"Fetching Race List for {target_date}...")
    
    # Option 2 (Diff) or 1 (Standard) for RACE to get keys
    # Use option 2 to be safe for past date setup? No, option 1 is standard if date is specified.
    # Actually, for "RACE", standard (1) asks for "From Time".
    res = jv.JVOpen("RACE", target_date, 1)
    
    # res can be tuple or int
    if isinstance(res, tuple):
        if res[0] != 0:
            print(f"Failed to get RACE list: {res[0]}")
            jv.JVClose()
            return
    elif res != 0:
        print(f"Failed to get RACE list: {res}")
        jv.JVClose()
        return

    race_keys = []
    buff = bytearray(100000)
    for i in range(100000):
        ret = jv.JVGets(buff, 100000)
        if isinstance(ret, tuple): rc = ret[0]
        else: rc = ret
        
        if rc == 0: break
        if rc == -1: continue
        if rc > 0:
            # data comes from ret[1]
            if isinstance(ret, tuple) and len(ret) > 1:
                data = bytes(ret[1])[:rc]
            else:
                data = buff[:rc] # Fallback
                
            rec_type = data[:2].decode('ascii', errors='ignore')
            # Suppress non-RA logs
            
            if rec_type == "RA":
                print(f"  Got Record: {rec_type} (Len={rc})")
                try:
                    y = data[11:15].decode('ascii')
                    m = data[15:17].decode('ascii')
                    d = data[17:19].decode('ascii')
                    j = data[19:21].decode('ascii')
                    r = data[25:27].decode('ascii')
                    
                    r_key = f"{y}{m}{d}{j}{r}"
                    print(f"    --> Key Extracted: {r_key}")
                    race_keys.append(r_key)
                    break # Stop after finding first key
                except Exception as e:
                    print(f"    Error parsing RA: {e}")
    
    jv.JVClose() # Open new connection for JVRTOpen
    
    if not race_keys:
        print("No races found for date.")
        return
        
    print(f"Found {len(race_keys)} races. Testing first one: {race_keys[0]}")
    
    # 2. Try JVRTOpen with Race Key
    target_key = race_keys[0]
    
    # Re-init? No, just Dispatch again or reuse? Reuse requires Close.
    # jv object persists.
    
    print(f"JVRTOpen('0B41', '{target_key}')...")
    res = jv.JVRTOpen("0B41", target_key)
    print(f"Result: {res}")
    
    if res == 0:
        print("SUCCESS! Found Data.")
        # Read a bit
        # ...
    else:
        print("Failed (-1 or other). Analysis: Maybe JVRTOpen DOES work with RaceKey!")

    jv.JVClose()

if __name__ == "__main__":
    check_race_access()
