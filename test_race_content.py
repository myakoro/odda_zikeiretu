import win32com.client
import os
from dotenv import load_dotenv

load_dotenv()

def check_race_content():
    key = os.getenv("JRAVAN_SERVICE_KEY").strip().replace('-', '')
    jv = win32com.client.Dispatch("JVDTLab.JVLink")
    jv.JVInit(key)
    
    # 2025/01/05 (Jan 5th)
    target = "20250105000000"
    
    print(f"Opening RACE spec (Opt=2) for {target}...")
    # Option 2 = Diff. Should fetch updates for that day.
    res = jv.JVOpen("RACE", target, 2)
    print(f"JVOpen Result: {res}")
    
    # Win32com returns tuple (code, read_count, download_count, last_timestamp)
    # or int code if error
    if isinstance(res, tuple):
        if res[0] != 0:
            print(f"Failed to open (Code={res[0]}).")
            return
    elif res != 0:
        print(f"Failed to open (Code={res}).")
        return

    buff = bytearray(100000)
    o1_map = {} # race_id -> list of timestamps
    
    # Read until end
    limit = 10000
    processed = 0
    
    while processed < limit:
        ret = jv.JVGets(buff, 100000)
        if isinstance(ret, tuple):
            rc = ret[0]
        else:
            rc = ret
            
        if rc == 0: break
        if rc == -1: continue # file switch
        
        if rc > 0:
            data = buff[:rc]
            rec_type = data[:2].decode('ascii', errors='ignore')
            
            if rec_type.startswith("O1"):
                try:
                    rid = data[11:27].decode('ascii', errors='ignore').strip()
                    ts = data[27:35].decode('ascii', errors='ignore') # MMDDHHMM
                    
                    if rid not in o1_map: o1_map[rid] = []
                    o1_map[rid].append(ts)
                except:
                    pass
        processed += 1

    print(f"\nAnalysis:")
    print(f"Total O1 Records: {sum(len(v) for v in o1_map.values())}")
    print(f"Total Races with O1: {len(o1_map)}")
    
    # Check for meaningful time series (more than 1 O1 per race)
    ts_races = [rid for rid, tss in o1_map.items() if len(tss) > 1]
    
    if ts_races:
        print(f"SUCCESS! Found {len(ts_races)} races with MULTIPLE O1 records.")
        sample_rid = ts_races[0]
        print(f"Sample Race {sample_rid} Timestamps: {o1_map[sample_rid]}")
    else:
        print("FAILURE: Each race has only 1 O1 record (Final Odds).")
        
    jv.JVClose()

if __name__ == "__main__":
    check_race_content()
