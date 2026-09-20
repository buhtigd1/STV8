import json
import datetime
import requests

# URL of the IPTV JSON file
URL = "https://raw.githubusercontent.com/darkbyteprojects/iptv_png/refs/heads/main/provider_2/live_events.json"

def fetch_json(url):
    """Download and parse JSON from the given URL."""
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def create_m3u(data, filename="stv8.m3u"):
    """Generate M3U playlist from JSON data."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in data:
            name = ch.get("name", "Unknown")
            url = ch.get("url", "")
            group = ch.get("group", "General")
            f.write(f'#EXTINF:-1 group-title="{group}", {name}\n{url}\n')

def create_log(data, filename="stv8.log"):
    """Generate log file with metadata and channel list."""
    with open(filename, "w", encoding="utf-8") as log:
        log.write(f"Generated on: {datetime.datetime.now()}\n")
        log.write(f"Total channels: {len(data)}\n\n")
        for ch in data:
            log.write(f'{ch.get("name","Unknown")} -> {ch.get("url","")}\n')

def main():
    data = fetch_json(URL)
    create_m3u(data)
    create_log(data)
    print("stv8.m3u and stv8.log created successfully.")

if __name__ == "__main__":
    main()
