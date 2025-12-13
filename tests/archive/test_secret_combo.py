import win32com.client
import os
from dotenv import load_dotenv

load_dotenv()

def fuzz_jvopen():
    key = os.getenv("JRAVAN_SERVICE_KEY").strip().replace('-', '')
    jv = win32com.client.Dispatch("JVDTLab.JVLink")
    jv.JVInit(key)
    
    date_14 = "20250105000000"
    date_8  = "20250105"
    
    specs = ["0B41", "0B12", "0B15", "0B30", "RACE"]
    options = [2, 3, 4] # 1=Normal, 2=Diff, 3=Setup, 4=SetupNoDialog
    
    print("Fuzzing JVOpen parameters for 2025/01/05...")
    
    for spec in specs:
        for opt in options:
            for time_fmt in [date_14, date_8]:
                try:
                    # Capture result
                    ret = jv.JVOpen(spec, time_fmt, opt)
                    
                    code = ret[0] if isinstance(ret, tuple) else ret
                    
                    if code != -111: # -111 is Invalid Param (Boring)
                        print(f"HIT! Spec={spec}, Opt={opt}, Time={len(time_fmt)}chars -> Result: {code}")
                        if code == 0:
                            print("  SUCCESS! Reading first record...")
                            buff = bytearray(100000)
                            r = jv.JVGets(buff, 100000)
                            if isinstance(r, tuple):
                                print(f"  Read: {r[0]}")
                            jv.JVClose()
                            return # Found it!
                    else:
                        # print(f"  Failed: Spec={spec}, Opt={opt}, Time={len(time_fmt)} -> -111")
                        pass
                        
                    jv.JVClose() # Reset for next
                except:
                    jv.JVClose()

    print("Fuzzing complete. If no HITS, then truly impossible via JVOpen.")

if __name__ == "__main__":
    fuzz_jvopen()
