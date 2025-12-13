import win32com.client
import os
from dotenv import load_dotenv

load_dotenv()

def test_bulk_keys():
    key = os.getenv("JRAVAN_SERVICE_KEY").strip().replace('-', '')
    jv = win32com.client.Dispatch("JVDTLab.JVLink")
    jv.JVInit(key)
    
    start_date = "20250101" # Jan 1st
    end_date = "20250131"   # Jan 31st
    
    print(f"Testing Bulk Key Fetch for {start_date}-{end_date}...")
    
    # Open from start_date
    res = jv.JVOpen("RACE", start_date + "000000", 1)
    if isinstance(res, tuple): res = res[0]
    
    if res != 0:
        print(f"JVOpen Failed: {res}")
        return

    buff = bytearray(100000)
    found_days = set()
    total_races = 0
    
    # Read loop
    while True:
        ret = jv.JVGets(buff, 100000)
        rc = ret[0] if isinstance(ret, tuple) else ret
        
        if rc == 0: break # End of Data
        if rc == -1: continue # Switch file
        
        if rc > 0:
            if isinstance(ret, tuple) and len(ret) > 1: data = bytes(ret[1])[:rc]
            else: data = buff[:rc]
            
            rec_type = data[:2].decode('ascii', errors='ignore')
            if rec_type == "RA":
                try:
                    y = data[11:15].decode('ascii')
                    m = data[15:17].decode('ascii')
                    d = data[17:19].decode('ascii')
                    
                    r_date = f"{y}{m}{d}"
                    
                    if r_date > end_date:
                        print(f"Reached {r_date}, stopping bulk fetch.")
                        break # Done
                        
                    found_days.add(r_date)
                    total_races += 1
                except:
                    pass

    print(f"Bulk Fetch Result:")
    print(f"  Total Races: {total_races}")
    print(f"  Holding Days: {sorted(list(found_days))}")
    print(f"  (This implies we safely skipped {31 - len(found_days)} non-race days without API calls!)")
    
    jv.JVClose()

if __name__ == "__main__":
    test_bulk_keys()
