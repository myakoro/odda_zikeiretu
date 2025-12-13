
import os
import sys
import time

# Correctly setup path to import collector
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import collector

# Load .env manually for the test
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(root_dir, '.env')
if os.path.exists(env_path):
    print(f"Loading env from {env_path}")
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("JRAVAN_SERVICE_KEY="):
                key = line.split("=", 1)[1].strip()
                if key.startswith('"') and key.endswith('"'): key = key[1:-1]
                if key.startswith("'") and key.endswith("'"): key = key[1:-1]
                os.environ["JRAVAN_SERVICE_KEY"] = key

def proof_of_concept():
    print("=== PROOF OF CONCEPT: Driver Behavior Verification ===")
    service_key = os.getenv("JRAVAN_SERVICE_KEY", "UNKNOWN").strip().replace('-', '')
    
    col = collector.JVLinkCollector(service_key)
    if not col.connect():
        print("Failed to connect")
        return

    target_date = "20260101" # Future date (Missing data)
    
    # TEST 1: JVOpen("0B41") - Expected to FAIL (-111)
    print(f"\n[TEST 1] Testing JVOpen('0B41', {target_date})... (Expect -111)")
    res = col.jvlink.JVOpen("0B41", target_date + "000000", 2)
    if isinstance(res, tuple): res = res[0]
    print(f"  Result: {res}")
    col.jvlink.JVClose()

    # TEST 1.5: JVOpen("RACE", ..., 1) - Expected to SUCCEED for cached data
    print(f"\n[TEST 1.5] Testing JVOpen(Option 1 - Local, 'RACE', {target_date})...")
    res = col.jvlink.JVOpen("RACE", target_date + "000000", 1)
    if isinstance(res, tuple): res = res[0]
    print(f"  Result: {res}")
    
    if res == 0:
        # Try to read straight away for Option 1
        buff_l = bytearray(48000)
        ret = col.jvlink.JVGets(buff_l, 48000)
        if isinstance(ret, tuple): rc_l = ret[0]
        else: rc_l = ret
        print(f"  Option 1 Read Result: {rc_l}")
        if rc_l > 0:
            print("  Option 1 SUCCESS: Found cached data!")
    col.jvlink.JVClose()
    
    # TEST 2: JVOpen("RACE") - Expected to SUCCEED (0)
    print(f"\n[TEST 2] Testing JVOpen(Option 2 - Download, 'RACE', {target_date})... (Expect 0)")
    res = col.jvlink.JVOpen("RACE", target_date + "000000", 2)
    if isinstance(res, tuple): res = res[0]
    print(f"  Result: {res}")
    
    if res == 0:
        print("  Downloading/Opening... Waiting 2s for stability...")
        time.sleep(2.0)
    
    found_race_id = None
    if res == 0:
        buff = bytearray(48000)
        # Loop to skip headers/metadata and find a real Race Record
        for i in range(100):
            ret = col.jvlink.JVGets(buff, 48000)
            
            # Flexible unpacking
            if isinstance(ret, tuple):
                 rc = ret[0]
                 if len(ret) > 1:
                     raw = ret[1]
                 else:
                     raw = buff
            else:
                 rc = ret
                 raw = buff

            if rc == 0: break # End of file
            if rc < 0: continue # Skip errors/files
            
            # rc > 0: Valid data
            raw_data = raw[:rc]
            try:
                # Standard RA format check
                rec_type = raw_data[:2].decode('ascii', errors='ignore')
                print(f"  [Loop {i}] Type: {rec_type} (Size: {rc})")
                
                if rec_type != 'RA':
                    continue # Skip non-race records
                
                # RA offset: Year(11-15), Month(15-17), Day(17-19)
                y = raw_data[11:15].decode('ascii')
                m = raw_data[15:17].decode('ascii')
                d = raw_data[17:19].decode('ascii')
                j = raw_data[19:21].decode('ascii')
                r = raw_data[25:27].decode('ascii')
                found_race_id = f"{y}{m}{d}{j}{r}"
                print(f"  Success! Found Race ID: {found_race_id} (Record Type: {rec_type})")
                break
            except Exception as e:
                # print(f"  Parsig error: {e}")
                pass
             
    col.jvlink.JVClose()
    
    # TEST 3: JVRTOpen("0B41", race_id) - Expected to SUCCEED
    if found_race_id:
        print(f"\n[TEST 3] Testing JVRTOpen('0B41', {found_race_id})...")
        res_rt = col.jvlink.JVRTOpen("0B41", found_race_id)
        if isinstance(res_rt, tuple): res_rt = res_rt[0]
        print(f"  Result: {res_rt}")
        if res_rt == 0:
             print("  Success! Ready to read odds.")
        col.jvlink.JVClose()
    else:
        print("\n[TEST 3] Skipped (No Race ID found)")

    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    proof_of_concept()
