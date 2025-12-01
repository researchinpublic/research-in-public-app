"""Start both backend API and frontend dev server."""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path
from dotenv import load_dotenv

# Try to import requests for health check, fallback to urllib if not available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    try:
        import urllib.request
        HAS_URLLIB = True
    except ImportError:
        HAS_URLLIB = False

load_dotenv()

def cleanup_processes(backend_process=None, frontend_process=None):
    print("\n\n🛑 Shutting down servers...")
    
    if backend_process and backend_process.poll() is None:
        try:
            if hasattr(os, 'killpg'):
                try:
                    os.killpg(os.getpgid(backend_process.pid), signal.SIGTERM)
                except (ProcessLookupError, OSError):
                    backend_process.terminate()
            else:
                backend_process.terminate()
            backend_process.wait(timeout=5)
        except (subprocess.TimeoutExpired, ProcessLookupError):
            try:
                backend_process.kill()
            except:
                pass
    
    if frontend_process and frontend_process.poll() is None:
        try:
            if hasattr(os, 'killpg'):
                try:
                    os.killpg(os.getpgid(frontend_process.pid), signal.SIGTERM)
                except (ProcessLookupError, OSError):
                    frontend_process.terminate()
            else:
                frontend_process.terminate()
            frontend_process.wait(timeout=5)
        except (subprocess.TimeoutExpired, ProcessLookupError):
            try:
                frontend_process.kill()
            except:
                pass
    
    try:
        import subprocess as sp
        result = sp.run(['lsof', '-ti:8000'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            for pid in result.stdout.strip().split('\n'):
                if pid:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                    except:
                        pass
        
        result = sp.run(['lsof', '-ti:3000'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            for pid in result.stdout.strip().split('\n'):
                if pid:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                    except:
                        pass
    except:
        pass
    
    print("✅ Servers stopped")


def main():
    print("🚀 Starting Research In Public Development Servers...")
    print("=" * 60)
    
    backend_process = None
    frontend_process = None
    
    try:
        print("\n🧹 Cleaning up ports 8000 and 3000...")
        try:
            import subprocess as sp
            result = sp.run(['lsof', '-ti:8000'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                for pid in result.stdout.strip().split('\n'):
                    if pid:
                        try:
                            print(f"   Killing process {pid} on port 8000")
                            os.kill(int(pid), signal.SIGKILL)
                        except:
                            pass
            
            result = sp.run(['lsof', '-ti:3000'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                for pid in result.stdout.strip().split('\n'):
                    if pid:
                        try:
                            print(f"   Killing process {pid} on port 3000")
                            os.kill(int(pid), signal.SIGKILL)
                        except:
                            pass
        except Exception as e:
            print(f"   Warning: Failed to cleanup ports: {e}")

        if not os.getenv("GEMINI_API_KEY"):
            print("⚠️  Warning: GEMINI_API_KEY not found in environment variables.")
            print("   Please set it in your .env file or environment variables.")
            response = input("\nContinue anyway? (y/n): ")
            if response.lower() != 'y':
                sys.exit(1)
        
        print("\n📡 Starting Backend API Server (FastAPI)...")
        print("   Backend logs will appear below in real time:")
        print("   " + "=" * 56)
        kwargs = {
            'cwd': Path(__file__).parent,
            'stdout': None,  # Print to console in real time
            'stderr': subprocess.STDOUT,  # Merge stderr into stdout
        }
        if sys.platform != 'win32':
            kwargs['preexec_fn'] = os.setsid  # Create new process group
        backend_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            **kwargs
        )
        
        print("   " + "=" * 56)
        print("   Waiting for backend to initialize...")
        max_wait = 30
        wait_interval = 1
        waited = 0
        backend_ready = False
        
        while waited < max_wait:
            time.sleep(wait_interval)
            waited += wait_interval
            
            if backend_process.poll() is not None:
                print("\n❌ Backend server failed to start!")
                print("   Check the logs above for error details.")
                cleanup_processes(backend_process, None)
                sys.exit(1)
            
            try:
                if HAS_REQUESTS:
                    response = requests.get("http://localhost:8000/", timeout=2)
                    if response.status_code == 200:
                        backend_ready = True
                        break
                elif HAS_URLLIB:
                    req = urllib.request.urlopen("http://localhost:8000/", timeout=2)
                    if req.getcode() == 200:
                        backend_ready = True
                        break
            except:
                pass
        
        if not backend_ready:
            print("⚠️  Warning: Backend may not be fully ready, but continuing...")
            print("   If you see connection errors, wait a few more seconds and refresh.")
        else:
            print(f"✅ Backend API ready after {waited} seconds")
        
        print("✅ Backend API running at http://localhost:8000")
        print("   API docs at http://localhost:8000/docs")
        
        print("\n🎨 Starting Frontend Dev Server (Next.js)...")
        frontend_dir = Path(__file__).parent / "frontend"
        
        if not frontend_dir.exists():
            print("❌ Frontend directory not found!")
            print("   Please ensure the frontend directory exists.")
            backend_process.terminate()
            sys.exit(1)
        
        env = os.environ.copy()
        nvm_path = r"C:\nvm4w\nodejs"
        if os.path.exists(nvm_path):
            current_path = env.get("PATH", "")
            if nvm_path not in current_path:
                env["PATH"] = f"{nvm_path};{current_path}"
        
        if not (frontend_dir / "node_modules").exists():
            print("⚠️  node_modules not found. Installing dependencies...")
            if sys.platform == "win32":
                install_process = subprocess.run(
                    ["powershell", "-Command", "npm install"],
                    cwd=frontend_dir,
                    env=env,
                    capture_output=True
                )
            else:
                install_process = subprocess.run(
                    ["npm", "install"],
                    cwd=frontend_dir,
                    env=env,
                    capture_output=True
                )
            if install_process.returncode != 0:
                print("❌ Failed to install frontend dependencies!")
                print(install_process.stderr.decode() if install_process.stderr else install_process.stdout.decode())
                backend_process.terminate()
                sys.exit(1)
            print("✅ Dependencies installed")
        
        frontend_kwargs = {
            'cwd': frontend_dir,
            'env': env,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE
        }
        if sys.platform != 'win32':
            frontend_kwargs['preexec_fn'] = os.setsid
        
        if sys.platform == "win32":
            frontend_process = subprocess.Popen(
                ["powershell", "-Command", "npm run dev"],
                **frontend_kwargs
            )
        else:
            frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                **frontend_kwargs
            )
        
        time.sleep(5)
        
        print("✅ Frontend running at http://localhost:3000")
        print("\n" + "=" * 60)
        print("🎉 Both servers are running!")
        print("\n📝 Next steps:")
        print("   - Frontend: http://localhost:3000")
        print("   - Backend API: http://localhost:8000")
        print("   - API Docs: http://localhost:8000/docs")
        print("\n⚠️  Press Ctrl+C to stop both servers")
        print("=" * 60)
        
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        cleanup_processes(backend_process, frontend_process)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        cleanup_processes(backend_process, frontend_process)
        sys.exit(1)


if __name__ == "__main__":
    main()

