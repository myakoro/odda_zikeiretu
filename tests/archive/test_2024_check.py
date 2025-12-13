import win32com.client
import os
from dotenv import load_dotenv

load_dotenv()

def check_2024():
    key = os.getenv("JRAVAN_SERVICE_KEY").strip().replace('-', '')
    jv = win32com.client.Dispatch("JVDTLab.JVLink")
    jv.JVInit(key)
    
    # 2024/01/06 (Saturday) - Allegedly worked in Step 1128
    target = "20240106"
    
    print(f"Checking {target} for 0B41 (JVRTOpen)...")
    res = jv.JVRTOpen("0B41", target)
    print(f"Result: {res}")
    
    if res == 0:
        print("Success! Data exists. Reading headers...")
        buff = bytearray(100000)
        # Read a few
        for i in range(5):
             ret = jv.JVGets(buff, 100000)
             if isinstance(ret, tuple):
                 print(f"Read {i}: code={ret[0]}")
                 if ret[0] > 0:
                     print(f"Data: {buff[:20]}")
    else:
        print("Failed.")
    
    jv.JVClose()

if __name__ == "__main__":
    check_2024()
