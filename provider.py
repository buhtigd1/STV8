import json
import datetime
import requests

URL = "https://raw.githubusercontent.com/darkbyteprojects/iptv_png/refs/heads/main/provider_2/live_events.json"

def fetch_json(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def create_m3u(data, filename="stv8.m3u"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for event in data:
            event_name = event.get("eventInfo", {}).get("eventName", "Unknown Event")
            event_cat = event.get("eventInfo", {}).get("eventCat", "General")
            teamA = event.get("eventInfo", {}).get("teamA", "")
            teamB = event.get("eventInfo", {}).get("teamB", "")
            match_label = f"{event_name} ({teamA} vs {teamB})" if teamA and teamB else event_name

            for stream in event.get("resolved_streams", []):
                title = stream.get("title", "Unknown Stream")
                url = stream.get("link", "")
                if url:
                    f.write(f'#EXTINF:-1 group-title="{event_cat}", {match_label} - {title}\n{url}\n')

def create_log(data, filename="stv8.log"):
    with open(filename, "w", encoding="utf-8") as log:
        log.write(f"Generated on: {datetime.datetime.now()}\n")
        total_streams = sum(len(event.get("resolved_streams", [])) for event in data)
        log.write(f"Total events: {len(data)}\n")
        log.write(f"Total streams: {total_streams}\n\n")

        for event in data:
            event_name = event.get("eventInfo", {}).get("eventName", "Unknown Event")
            teamA = event.get("eventInfo", {}).get("teamA", "")
            teamB = event.get("eventInfo", {}).get("teamB", "")
            match_label = f"{event_name} ({teamA} vs {teamB})" if teamA and teamB else event_name

            log.write(f"Event: {match_label}\n")
            for stream in event.get("resolved_streams", []):
                title = stream.get("title", "Unknown Stream")
                url = stream.get("link", "")
                log.write(f"  {title} -> {url}\n")
            log.write("\n")

def main():
    data = fetch_json(URL)
    create_m3u(data)
    create_log(data)
    print("stv8.m3u and stv8.log created successfully.")

if __name__ == "__main__":
    main()
