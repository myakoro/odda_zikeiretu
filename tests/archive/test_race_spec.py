import win32com.client
import os
from dotenv import load_dotenv

load_dotenv()

def check_race_accumulation():
    key = os.getenv("JRAVAN_SERVICE_KEY").strip().replace('-', '')
    jv = win32com.client.Dispatch("JVDTLab.JVLink")
    jv.JVInit(key)
    
    # Target: Last Sunday
    target = "20251207000000"
    
    print(f"Testing JVOpen('RACE', {target}, option=4)...")
    try:
        # Option 4 = Setup (Accumulation?)
        res = jv.JVOpen("RACE", target, 4)
        print(f"Result: {res}")
        
        if hasattr(res, '__iter__'):
             print(f"Code={res[0]}, Read={res[1]}, DL={res[2]}")
             if res[0] != 0:
                 print("Error.")
                 return
        elif res != 0:
             print("Error.")
             return
             
        buff = bytearray(100000)
        o1_counts = {} # race_id -> count
        
        limit = 50000
        processed = 0
        
        while processed < limit:
            ret = jv.JVGets(buff, 100000)
            if isinstance(ret, tuple):
                rc = ret[0]
            else:
                rc = ret
                
            if rc == 0: break
            if rc == -1: continue
            if rc > 0:
                data = buff[:rc]
                rec_type = data[:2].decode('ascii', errors='ignore')
                
                if rec_type.startswith("O1"):
                    # Extract Race ID
                    try:
                        rid = data[11:27].decode('ascii', errors='ignore')
                        if rid not in o1_counts: o1_counts[rid] = 0
                        o1_counts[rid] += 1
                        
                        # Print timestamp of first few
                        if o1_counts[rid] <= 3:
                            ts = data[27:35].decode('ascii', errors='ignore')
                            print(f"  Race {rid}: O1 Timestamp={ts}")
                    except:
                        pass
                
                processed += 1
                if processed % 1000 == 0:
                    print(f"  Processed {processed} records...")

        print("\nAnalysis Result:")
        multi_update_races = 0
        for rid, count in o1_counts.items():
            if count > 1:
                multi_update_races += 1
        
        print(f"Total Races with O1: {len(o1_counts)}")
        print(f"Races with Multiple O1 (Time Series): {multi_update_races}")
        
        if multi_update_races > 0:
            print("SUCCESS: RACE spec contains Time Series!")
        else:
            print("FAILURE: RACE spec contains only Final Odds.")

    except Exception as e:
        print(f"Error: {e}")
    
    jv.JVClose()

if __name__ == "__main__":
    check_race_accumulation()
