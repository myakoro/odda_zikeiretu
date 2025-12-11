import win32com.client
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
service_key = os.getenv("JRAVAN_SERVICE_KEY", "").strip().replace('-', '')

try:
    jvlink = win32com.client.Dispatch("JVDTLab.JVLink")
    res = jvlink.JVInit(service_key)
    print(f"JVInit: {res}")
    
    if res == 0:
        key = datetime.now().strftime("%Y%m%d")
        print(f"Testing JVRTOpen 0B11 with key: {key}")
        res_open = jvlink.JVRTOpen("0B11", key)
        print(f"JVRTOpen 0B11: {res_open}")
        jvlink.JVClose()
    
except Exception as e:
    print(f"Error: {e}")
