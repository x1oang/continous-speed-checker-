import time
import csv
from datetime import datetime
import speedtest
import os
import sys
import traceback


LOG_FILE = "speed_log.csv"
INTERVAL = 60                   
MAX_RETRIES = 3                 


def ensure_csv_header(path):
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["timestamp_utc", "timestamp_local", "server_id", "server_name",
                        "server_country", "server_sponsor", "ping_ms", "download_Mbps",
                        "upload_Mbps", "bytes_received", "bytes_sent", "error"])

def run_test():
    s = speedtest.Speedtest()
    s.get_best_server()
    server = s.best
    server_id = server.get("id", "")
    server_name = server.get("name", "")
    server_country = server.get("country", "")
    server_sponsor = server.get("sponsor", "")
    ping = None
    download_mbps = None
    upload_mbps = None
    bytes_received = ""
    bytes_sent = ""
    err = ""
    try:
        download_bps = s.download(threads=None)
        upload_bps = s.upload(threads=None, pre_allocate=False)
        results = s.results.dict()
        ping = results.get("ping")
        download_mbps = round(download_bps / 1e6, 3)
        upload_mbps = round(upload_bps / 1e6, 3)
        bytes_received = results.get("bytes_received", "")
        bytes_sent = results.get("bytes_sent", "")
    except Exception as e:
        err = str(e)
        print("Error during speedtest:", err)
        traceback.print_exc()
    return {
        "server_id": server_id,
        "server_name": server_name,
        "server_country": server_country,
        "server_sponsor": server_sponsor,
        "ping": ping,
        "download": download_mbps,
        "upload": upload_mbps,
        "bytes_received": bytes_received,
        "bytes_sent": bytes_sent,
        "error": err
    }

def append_csv(path, row):
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        w.writerow(row)

def main():
    print("Starting continuous speedtester. Press Ctrl+C to stop.")
    ensure_csv_header(LOG_FILE)
    while True:
        for attempt in range(1, MAX_RETRIES+1):
            try:
                t_utc = datetime.utcnow().isoformat()
                t_local = datetime.now().isoformat()
                result = run_test()
                append_csv(LOG_FILE, [
                    t_utc, t_local,
                    result["server_id"], result["server_name"],
                    result["server_country"], result["server_sponsor"],
                    result["ping"], result["download"],
                    result["upload"], result["bytes_received"],
                    result["bytes_sent"], result["error"]
                ])
                print(f"[{t_local}] ping={result['ping']} ms  dl={result['download']} Mbps  ul={result['upload']} Mbps  server={result['server_name']} {result['server_country']}")
                break
            except Exception as e:
                print(f"Attempt {attempt} failed: {e}")
                if attempt == MAX_RETRIES:
                    t_utc = datetime.utcnow().isoformat()
                    t_local = datetime.now().isoformat()
                    append_csv(LOG_FILE, [t_utc, t_local, "", "", "", "", "", "", "", "", "", f"fatal:{e}"])
                else:
                    time.sleep(5)


        if INTERVAL > 0:
            time.sleep(INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user. CSV saved.")
        sys.exit(0)
