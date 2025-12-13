import win32com.client
import os
from dotenv import load_dotenv

load_dotenv()

def analyze_date(jv, date_str, label):
    print(f"\n[{label}] Testing {date_str} (Spec=0B41)...")
    res = jv.JVRTOpen("0B41", date_str)
    print(f"  JVRTOpen Result: {res}")
    
    if res != 0:
        print("  -> NO DATA (Server returned error/skip)")
        return

    # Read up to 50 records to analyze content
    print("  -> Data Found! analyzing records...")
    buff = bytearray(100000)
    
    o1_count = 0
    timestamps = set()
    
    for i in range(500): # Read enough to find multiple timestamps
        ret = jv.JVGets(buff, 100000)
        
        # Win32com return handling
        if isinstance(ret, tuple):
            rc = ret[0]
        else:
            rc = ret
            
        if rc == 0: break # End of file
        if rc == -1: continue # File switch
        if rc > 0:
            data = buff[:rc]
            rec_type = data[:2].decode('ascii', errors='ignore')
            
            if rec_type.startswith("O1"):
                o1_count += 1
                # Extract timestamp (Offset 27-35: MMDDHHMM)
                try:
                    ts = data[27:35].decode('ascii', errors='ignore')
                    timestamps.add(ts)
                except:
                    pass
                
                if o1_count == 1:
                    print(f"  Sample O1 Record found (Len={rc})")

        if len(timestamps) >= 3:
            break
            
    print(f"  Analysis Result:")
    print(f"  - Total O1 Records scanned: {o1_count}")
    print(f"  - Unique Timestamps found: {len(timestamps)} {list(timestamps)}")
    
    if len(timestamps) > 1:
        print("  -> CONFIRMED: Contains Time-Series Data (Multiple updates found)")
    else:
        print("  -> WARNING: Only 1 timestamp found (Might be Final Odds only)")

    jv.JVClose()

if __name__ == "__main__":
    key = os.getenv("JRAVAN_SERVICE_KEY").strip().replace('-', '')
    jv = win32com.client.Dispatch("JVDTLab.JVLink")
    jv.JVInit(key)
    
    # 1. Test Recent (Last Sunday) to prove it works at all
    # Today is 2025-12-12 (Fri). Last Sunday was 2025-12-07.
    analyze_date(jv, "20251207", "RECENT")
    
    # 2. Test Target (Jan 2025)
    analyze_date(jv, "20250105", "TARGET JAN 2025")
    
    # 3. Test Old (Jan 2024) - Just in case
    # analyze_date(jv, "20240106", "OLD JAN 2024")
