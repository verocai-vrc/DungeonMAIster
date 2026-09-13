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

    # Prefer the venv Python if one exists alongside this script
    venv_python = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = os.path.join(base_dir, ".venv", "bin", "python")
    python_exe = venv_python if os.path.exists(venv_python) else sys.executable

    print("========================================")
    print(">>>  Starting DungeonMAIster...")
    print("========================================")
    print("Bringing up the backend server (FastAPI)...")

    server_process = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "backend.main:app", "--reload"],
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
