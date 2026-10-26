import base64
import hashlib
import hmac
import json
import os
import random
import time
import uuid
import requests

# Load sensitive credentials securely from Environment Variables
SECRET_KEY = os.getenv("SECRET_KEY", "").encode("utf-8")
PROXY_USER = os.getenv("PROXY_USER", "")
PROXY_PASS = os.getenv("PROXY_PASS", "")

URL = "https://views.securevid-teleplayer.workers.dev/collect"

# Proxy Configuration Host/Port (Safe to keep public)
PROXY_HOST = "gw.dataimpulse.com"
PROXY_PORT = "823"

# Construct proxy URL
PROXY_URL = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
PROXIES = {
    "http": PROXY_URL,
    "https": PROXY_URL,
}

# Videos with their total lengths converted to seconds
VIDEOS = {
    "https://vidbunker.in/watch/jVpnNsOpZ": 5040,   # 1 hour 24 minutes (5,040s)
    "https://vidbunker.in/watch/fvfdvfff": 9900,  # 2 hours 45 minutes (9,900s)
    "https://vidbunker.in/watch/vdjcdexd": 1500,  # 25 minutes (1,500s)
    "https://vidbunker.in/watch/vfjemc": 6660,    # 1 hour 51 minutes (6,660s)
}


def send_collect_request():
    if not SECRET_KEY:
        print("[-] Error: SECRET_KEY environment variable is not set!")
        return

    # 1. Pick a random video and its maximum duration
    video_id, max_duration_sec = random.choice(list(VIDEOS.items()))

    # 2. Generate a realistic random played_sec
    played_sec = random.randint(10, max_duration_sec)

    # 3. Generate current Unix timestamp
    timestamp = str(int(time.time()))

    # 4. Build the request body dictionary
    body_dict = {
        "event_id": str(uuid.uuid4()),
        "device_id": str(uuid.uuid4()),
        "video_id": video_id,
        "played_sec": played_sec,
    }

    # 5. Create a strictly compact JSON string (no spaces)
    body_str = json.dumps(body_dict, separators=(",", ":"))

    # 6. Construct message string to sign: timestamp + "." + body_str
    message = f"{timestamp}.{body_str}".encode("utf-8")

    # 7. Compute HMAC-SHA256 using the raw secret key
    signature_bytes = hmac.new(SECRET_KEY, message, hashlib.sha256).digest()

    # 8. Convert raw bytes to URL-safe Base64 and strip trailing padding '='
    x_signature = (
        base64.urlsafe_b64encode(signature_bytes).decode("utf-8").rstrip("=")
    )

    # 9. Set up the headers
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "x-timestamp": timestamp,
        "x-signature": x_signature,
        "User-Agent": "okhttp/4.12.0",
    }

    print(f"[*] Selected Video: {video_id} (Max: {max_duration_sec}s)")
    print(f"[*] Generated Played Seconds: {played_sec}s")
    print(f"[*] Generated Timestamp: {timestamp}")
    print(f"[*] Generated Signature: {x_signature}")
    print(f"[*] Payload Body:\n{body_str}\n")
    print(f"[*] Sending POST request to {URL} via proxy...")

    # 10. Send the POST request using `data` with the exact compact string and proxies
    try:
        response = requests.post(URL, headers=headers, data=body_str, proxies=PROXIES, timeout=30)
        # 11. Output the results
        print(f"[+] Response Status Code: {response.status_code}")
        print(f"[+] Response Body Text:\n{response.text}")
    except requests.exceptions.RequestException as e:
        print(f"[-] Request failed: {e}")


if __name__ == "__main__":
    send_collect_request()
