import os
import subprocess
import sys
import webbrowser
import time
from pathlib import Path

def setup_and_run():
    # Define paths
    root_dir = Path(__file__).parent.absolute()
    backend_dir = root_dir / "backend"
    frontend_path = root_dir / "frontend" / "index.html"
    venv_dir = backend_dir / ".venv"
    
    # Path to python in venv
    if os.name == 'nt':
        python_executable = venv_dir / "Scripts" / "python.exe"
    else:
        python_executable = venv_dir / "bin" / "python"

    print("=" * 60)
    print("🚀 Reinforcement Learning Quiz Master - Setup & Run")
    print("=" * 60)

    # Step 1: Create venv if it doesn't exist
    if not venv_dir.exists():
        print(f"[*] Creating virtual environment in {venv_dir}...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    # Step 2: Install/Update dependencies
    print("[*] Installing/Updating dependencies...")
    try:
        subprocess.run([str(python_executable), "-m", "pip", "install", "-r", str(backend_dir / "requirements.txt")], check=True)
    except subprocess.CalledProcessError:
        print("[!] Error installing dependencies. Make sure you have an internet connection.")
        return

    # Step 3: Start backend in a separate process
    print("[*] Starting FastAPI backend server...")
    # Using Popen so it runs asynchronously
    backend_process = subprocess.Popen([str(python_executable), "main.py"], cwd=backend_dir)

    # Step 4: Give the backend a few seconds to initialize
    print("[*] Waiting for server to warm up...")
    time.sleep(3)

    # Step 5: Open Frontend in the default browser
    print(f"[*] Opening frontend in your browser...")
    webbrowser.open(frontend_path.as_uri())

    print("\n" + "✨" * 20)
    print("SUCCESS: Your app is now live!")
    print(f"Backend: http://localhost:8000")
    print(f"Frontend: {frontend_path.as_uri()}")
    print("\nKeep this terminal open to keep the backend running.")
    print("Press Ctrl+C to stop the server.")
    print("✨" * 20 + "\n")

    try:
        # Stay alive while the backend is running
        backend_process.wait()
    except KeyboardInterrupt:
        print("\n[*] Gracefully shutting down the backend...")
        backend_process.terminate()
        print("[*] Shutdown complete. Goodbye!")

if __name__ == "__main__":
    setup_and_run()
