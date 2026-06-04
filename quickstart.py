import os
import sys
import time
import webbrowser
import subprocess

# Force UTF-8 output on Windows to avoid errors with special characters
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def start():
    # Determine the directories based on this script's location
    base_dir = os.path.abspath(os.path.dirname(__file__))

    print("========================================")
    print(">>>  Starting DungeonMAIster...")
    print("========================================")
    print("Bringing up the backend server (FastAPI)...")

    # Start Uvicorn using the current Python executable (keeps venv compatibility)
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload"],
        cwd=base_dir
    )

    # Wait 2 seconds to give the server time to start properly
    time.sleep(2)

    print("Opening the interface in the browser...")
    webbrowser.open("http://localhost:8000")

    try:
        print("\nThe server is running! Press Ctrl+C in this terminal to shut down the game.")
        server_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down the DungeonMAIster engine...")
        server_process.terminate()

if __name__ == "__main__":
    start()
