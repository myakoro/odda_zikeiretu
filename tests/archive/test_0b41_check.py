import win32com.client
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    key = os.getenv("JRAVAN_SERVICE_KEY").strip().replace('-', '')
    jv = win32com.client.Dispatch("JVDTLab.JVLink")
    jv.JVInit(key)
    
    # Try 2024 (Recent-ish) and 2020 (Old)
    dates = ["20240106", "20200105"]
    specs = ["0B41", "0B12", "0B51"] # 0B51 is "Sokukho Oz" sometimes? 0B41 is standard.
    
    for date in dates:
        print(f"\n====== Testing Date: {date} ======")
        for spec in specs:
            print(f"--- Spec: {spec} ---")
            # JVOpen check
            try:
                ret = jv.JVOpen(spec, f"{date}000000", 4)
                code = ret[0] if isinstance(ret, tuple) else ret
                print(f"  JVOpen({spec}, opt=4): {code}")
                if code == 0:
                     print(f"  *** FOUND SUCCESS: JVOpen {spec} ***")
                jv.JVClose()
            except Exception as e:
                print(f"  JVOpen Err: {e}")
                
            # JVRTOpen check
            try:
                ret = jv.JVRTOpen(spec, date)
                print(f"  JVRTOpen({spec}): {ret}")
                if ret == 0:
                     print(f"  *** FOUND SUCCESS: JVRTOpen {spec} ***")
                try: jv.JVClose() 
                except: pass
            except:
                pass
