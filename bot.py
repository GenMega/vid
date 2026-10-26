import base64
import hashlib
import hmac
import json
import os
import random
import sys
import time
import uuid
import requests

# Load sensitive credentials securely from Environment Variables
SECRET_KEY = os.getenv("SECRET_KEY", "").encode("utf-8")
PROXY_USER = os.getenv("PROXY_USER", "")
PROXY_PASS = os.getenv("PROXY_PASS", "")

URL = "https://views.securevid-teleplayer.workers.dev/collect"

# Proxy Configuration Host/Port
PROXY_HOST = "gw.dataimpulse.com"
PROXY_PORT = "823"

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

    # 1. Generate a unique session ID for DataImpulse to force a brand new IP address
    session_id = str(uuid.uuid4())
    dynamic_proxy_user = f"{PROXY_USER};sessid.{session_id}"

    # Construct proxy URL with the rotating session tag
    proxy_url = f"http://{dynamic_proxy_user}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }

    # 2. Pick a random video and its maximum duration
    video_id, max_duration_sec = random.choice(list(VIDEOS.items()))

    # 3. Generate a realistic random played_sec
    played_sec = random.randint(10, max_duration_sec)

    # 4. Generate current Unix timestamp
    timestamp = str(int(time.time()))

    # 5. Build the request body dictionary
    body_dict = {
        "event_id": str(uuid.uuid4()),
        "device_id": str(uuid.uuid4()),
        "video_id": video_id,
        "played_sec": played_sec,
    }

    # 6. Create a strictly compact JSON string (no spaces)
    body_str = json.dumps(body_dict, separators=(",", ":"))

    # 7. Construct message string to sign: timestamp + "." + body_str
    message = f"{timestamp}.{body_str}".encode("utf-8")

    # 8. Compute HMAC-SHA256 using the raw secret key
    signature_bytes = hmac.new(SECRET_KEY, message, hashlib.sha256).digest()

    # 9. Convert raw bytes to URL-safe Base64 and strip trailing padding '='
    x_signature = (
        base64.urlsafe_b64encode(signature_bytes).decode("utf-8").rstrip("=")
    )

    # 10. Set up the headers
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "x-timestamp": timestamp,
        "x-signature": x_signature,
        "User-Agent": "okhttp/4.12.0",
    }

    print(f"\n----------------------------------------")
    print(f"[*] New Request Initiated")
    print(f"[*] Proxy IP Session ID: {session_id[:8]}...")
    print(f"[*] Selected Video: {video_id} (Max: {max_duration_sec}s)")
    print(f"[*] Generated Played Seconds: {played_sec}s")
    print(f"[*] Generated Timestamp: {timestamp}")
    print(f"[*] Generated Signature: {x_signature}")

    # 11. Send the POST request using a fresh session to ensure socket renewal
    try:
        session = requests.Session()
        response = session.post(URL, headers=headers, data=body_str, proxies=proxies, timeout=30)
        print(f"[+] Response Status Code: {response.status_code}")
        print(f"[+] Response Body Text: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"[-] Request failed: {e}")


def main():
    start_time = time.time()
    MAX_RUN_TIME = 5.5 * 3600  # 5.5 hours in seconds (safely below GitHub's 6-hour limit)

    print("[*] Starting 24x7 automated runner loop...")
    print(f"[*] Safety timeout set to {MAX_RUN_TIME / 3600} hours before auto-restart.")

    while True:
        # Check if 5.5 hours have elapsed
        if time.time() - start_time >= MAX_RUN_TIME:
            print("[*] Reached 5.5 hours execution limit. Exiting cleanly for auto-restart.")
            sys.exit(0)

        # Execute the request workflow
        send_collect_request()

        # Wait 50 seconds before making the next request
        print("[*] Waiting 50 seconds before next request...")
        time.sleep(50)


if __name__ == "__main__":
    main()
