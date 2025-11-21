import requests, hashlib, platform, subprocess, re, uuid, os, json
import jwt
from cryptography.fernet import Fernet
from pathlib import Path
from base64 import urlsafe_b64encode

PUBLIC_KEY_PATH = "public_key.pem"  
SERVER_URL = "https://updates.example.com"
LOCAL_STORE = Path.home() / ".stur"
LOCAL_STORE.mkdir(parents=True, exist_ok=True)
LICENSE_FILE = LOCAL_STORE / "license.token.enc"
FERNET_KEY_FILE = LOCAL_STORE / "secret.key"

def get_mac():
    mac = uuid.getnode()
    return ":".join("%02x" % ((mac >> ele) & 0xff) for ele in range(0,8*6,8))[::-1]

def get_machine_id():
    sys = platform.system()
    try:
        if sys == "Linux":
            return open('/etc/machine-id').read().strip()
        if sys == "Darwin":
            out = subprocess.check_output(['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice']).decode()
            m = re.search(r'"IOPlatformUUID" = "([^"]+)"', out)
            return m.group(1)
        if sys == "Windows":
            out = subprocess.check_output('wmic csproduct get uuid').decode().splitlines()
            return out[1].strip()
    except Exception:
        return ""

def make_fingerprint():
    items = [get_mac(), get_machine_id(), platform.node()]
    s = "|".join(items).encode('utf-8')
    print(items, '\n', s)
    return hashlib.sha256(s).hexdigest()

def get_or_create_fernet_key():
    if FERNET_KEY_FILE.exists():
        return FERNET_KEY_FILE.read_bytes()
    key = Fernet.generate_key()
    FERNET_KEY_FILE.write_bytes(key)
    return key

def store_token_encrypted(token):
    key = get_or_create_fernet_key()
    f = Fernet(key)
    TOKEN = token if isinstance(token, bytes) else token.encode()
    LICENSE_FILE.write_bytes(f.encrypt(TOKEN))

def load_token_decrypted():
    if not LICENSE_FILE.exists():
        return None
    key = get_or_create_fernet_key()
    f = Fernet(key)
    return f.decrypt(LICENSE_FILE.read_bytes()).decode()

def verify_token_signature(token):
    pub = open(PUBLIC_KEY_PATH,"rb").read()
    try:
        payload = jwt.decode(token, pub, algorithms=["RS256"])
        return payload
    except Exception as e:
        print("Invalid token:", e)
        return None

def activate(license_key):
    fp = make_fingerprint()
    resp = requests.post(f"{SERVER_URL}/activate", json={"license_key": license_key, "fingerprint_hash": fp}, timeout=10)
    if resp.status_code != 200:
        raise SystemExit("Activation failed: " + resp.text)
    token = resp.json()["token"]
    payload = verify_token_signature(token)
    if not payload:
        raise SystemExit("Token signature invalid")
    # ensure payload fp matches local fp
    if payload.get("fp") != fp:
        raise SystemExit("Fingerprint mismatch in token")
    store_token_encrypted(token)
    print("Activated successfully. Expires:", payload.get("exp"))
    return payload

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: activate.py <LICENSE_KEY>")
        raise SystemExit(1)
    k = sys.argv[1].strip()
    activate(k)
