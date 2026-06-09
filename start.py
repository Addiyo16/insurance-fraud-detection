import subprocess
import time
import sys
import os

# Set environment variable to ensure output is written to logs immediately
os.environ["PYTHONUNBUFFERED"] = "1"

print("🔄 Launching ShieldAI Container Services...")

# 1. Start FastAPI REST Server in the background
print("🚀 Starting FastAPI REST database service on http://127.0.0.1:8000 ...")
api_cmd = [
    sys.executable, "-m", "uvicorn", "api.main:app",
    "--host", "127.0.0.1", "--port", "8000"
]
api_process = subprocess.Popen(api_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

# 2. Wait for FastAPI to bind
time.sleep(3.0)

# 3. Start Streamlit Dashboard in the foreground
print("🚀 Starting Streamlit Dashboard on port 8080...")
streamlit_cmd = [
    sys.executable, "-m", "streamlit", "run", "app.py",
    "--server.port", "8080", "--server.address", "0.0.0.0"
]
streamlit_process = subprocess.Popen(streamlit_cmd)

# 4. Monitor both processes
print("✅ ShieldAI services successfully orchestrated!")
try:
    while True:
        # Check if either process has died
        api_exit = api_process.poll()
        streamlit_exit = streamlit_process.poll()
        
        if api_exit is not None:
            print(f"❌ FastAPI server stopped unexpectedly with code {api_exit}!")
            # Print last few lines of output
            if api_process.stdout:
                print("API Logs:")
                for line in api_process.stdout.readlines()[-20:]:
                    print(f"  [API] {line.strip()}")
            break
            
        if streamlit_exit is not None:
            print(f"❌ Streamlit dashboard stopped unexpectedly with code {streamlit_exit}!")
            break
            
        time.sleep(2.0)
except KeyboardInterrupt:
    print("\n👋 Received shutdown signal. Stopping services...")
finally:
    # Cleanup processes
    print("🧹 Cleaning up running processes...")
    try:
        api_process.terminate()
        api_process.wait(timeout=2.0)
    except Exception:
        api_process.kill()
        
    try:
        streamlit_process.terminate()
        streamlit_process.wait(timeout=2.0)
    except Exception:
        streamlit_process.kill()
        
    print("✅ Cleanup complete. Exiting start.py.")
