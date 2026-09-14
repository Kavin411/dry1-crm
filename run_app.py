import os
import sys
import subprocess
import time
import threading
import streamlit.web.cli as stcli

def resolve_path(relative_path):
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def open_app_window():
    time.sleep(2.5)  # Wait for Streamlit server to start
    # Edge Browser-a Thani App Window Mode-la Open Pannum
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if os.path.exists(edge_path):
        subprocess.Popen([edge_path, "--app=http://localhost:8501"])
    else:
        # Microsoft Edge illana Chrome-la App mode-la open pannum
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if os.path.exists(chrome_path):
            subprocess.Popen([chrome_path, "--app=http://localhost:8501"])

if __name__ == "__main__":
    # Background thread to open custom app window
    threading.Thread(target=open_app_window, daemon=True).start()
    
    app_path = resolve_path("app.py")
    sys.argv = ["streamlit", "run", app_path, "--global.developmentMode=false", "--server.headless=true"]
    sys.exit(stcli.main())