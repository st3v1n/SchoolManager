# client/updater.py
import requests, json, hashlib, os, shutil, tempfile, subprocess, time
from pathlib import Path
import jwt

PUBLIC_KEY_PATH = "public_key.pem"
MANIFEST_URL = "https://updates.example.com/manifest/latest"
LOCAL_ROOT = Path(__file__).parent
SERVER_DIR = LOCAL_ROOT / "server" 
BACKUP_DIR = LOCAL_ROOT / "server_backup"
TMP_DIR = LOCAL_ROOT / "tmp_update"
VERSION_FILE = SERVER_DIR / "version.txt"
HEALTH_URL = "http://127.0.0.1:8000/health"
PLATFORM_KEY = "windows" if os.name == "nt" else "linux" if os.name == "posix" else "unknown"

def get_local_version():
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text().strip()
    return "0.0.0"

def verify_manifest_signature(signed):
    # signed = {"manifest": {...}, "signature": "..."}
    pub = open(PUBLIC_KEY_PATH,"rb").read()
    sig = signed["signature"]
    # We'll verify signature by re-encoding manifest and verifying the signature using jwt
    # The server encoded a small signed payload; decode to ensure signed by private key.
    try:
        decoded = jwt.decode(sig, pub, algorithms=["RS256"])
        # for demo, server used sha256 of sorted manifest. check equality
        manifest_json_sorted = json.dumps(signed["manifest"], sort_keys=True).encode("utf-8")
        local_hash = hashlib.sha256(manifest_json_sorted).hexdigest()
        if decoded.get("sig") != local_hash:
            raise Exception("Manifest hash mismatch")
        return True
    except Exception as e:
        print("Manifest signature verify failed:", e)
        return False

def download_file(url, dest_path):
    r = requests.get(url, stream=True, timeout=30)
    with open(dest_path, "wb") as f:
        h = hashlib.sha256()
        for chunk in r.iter_content(8192):
            if not chunk:
                break
            f.write(chunk)
            h.update(chunk)
    return h.hexdigest()

def stop_server():
    # Implement your graceful stop (signal or subprocess management)
    # For demo, we'll attempt to hit /shutdown endpoint or kill by PID recorded in server/pid.txt
    pid_file = SERVER_DIR / "server.pid"
    if pid_file.exists():
        pid = int(pid_file.read_text().strip())
        try:
            os.kill(pid, 15)
            time.sleep(1)
        except Exception:
            pass
    # Wait short time
    time.sleep(1)

def start_server():
    # Start server process (use your bundled Python to run manage.py)
    # For demo assume manage.py in SERVER_DIR and sys.executable is fine
    p = subprocess.Popen(["python", "manage.py", "runserver", "0.0.0.0:8000"], cwd=str(SERVER_DIR))
    # Save PID
    (SERVER_DIR / "server.pid").write_text(str(p.pid))
    time.sleep(1)
    return p

def check_health(timeout=10):
    import requests
    for _ in range(timeout * 2):
        try:
            r = requests.get(HEALTH_URL, timeout=1)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

def apply_update(pkg_path):
    # Extract to TMP_DIR
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)
    TMP_DIR.mkdir(parents=True)
    shutil.unpack_archive(str(pkg_path), str(TMP_DIR))
    # atomic swap: backup current -> BACKUP_DIR, move TMP -> SERVER_DIR
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)
    if SERVER_DIR.exists():
        SERVER_DIR.rename(BACKUP_DIR)
    TMP_DIR.rename(SERVER_DIR)
    return True

def rollback():
    if BACKUP_DIR.exists():
        if SERVER_DIR.exists():
            shutil.rmtree(SERVER_DIR)
        BACKUP_DIR.rename(SERVER_DIR)

def main_check_update():
    local_version = get_local_version()
    r = requests.get(MANIFEST_URL, timeout=10)
    signed = r.json()  # {"manifest": {...}, "signature": "..."}
    if not verify_manifest_signature(signed):
        print("Manifest signature invalid")
        return
    manifest = signed["manifest"]
    new_version = manifest["version"]
    if new_version == local_version:
        print("Up to date")
        return
    print(f"New version {new_version} available (local {local_version})")
    plat = PLATFORM_KEY
    info = manifest["platforms"].get(plat)
    if not info:
        print("No package for this platform")
        return
    url = info["url"]
    expected_sha = info["sha256"]
    tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".pkg")
    tmpf.close()
    print("Downloading...", url)
    actual_sha = download_file(url, tmpf.name)
    if actual_sha != expected_sha:
        print("Checksum mismatch!")
        return
    print("Stopping server for update...")
    stop_server()
    try:
        apply_update(tmpf.name)
        print("Starting new server...")
        p = start_server()
        if check_health():
            print("Update applied successfully")
            # cleanup backup
            if BACKUP_DIR.exists():
                shutil.rmtree(BACKUP_DIR)
            # update version.txt if necessary
            (SERVER_DIR / "version.txt").write_text(new_version)
        else:
            print("Health check failed, rolling back...")
            stop_server()
            rollback()
            start_server()
            print("Rollback complete")
    finally:
        try:
            os.unlink(tmpf.name)
        except Exception:
            pass

if __name__ == "__main__":
    main_check_update()
