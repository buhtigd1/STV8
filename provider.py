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
            logo = event.get("eventInfo", {}).get("eventLogo", "")
            teamA = event.get("eventInfo", {}).get("teamA", "")
            teamB = event.get("eventInfo", {}).get("teamB", "")
            match_label = f"{event_name}: {teamA} vs {teamB}" if teamA and teamB else event_name
            tvg_id = str(event.get("id", ""))

            for stream in event.get("resolved_streams", []):
                title = stream.get("title", "Unknown Stream")
                url = stream.get("link", "")
                api = stream.get("api", "")
                if not url:
                    continue

                tvg_name = f"{match_label} - {title}"
                f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{tvg_name}" tvg-logo="{logo}" group-title="{event_cat}",{tvg_name}\n')

                # DASH/MPD streams
                if url.endswith(".mpd"):
                    f.write("#KODIPROP:inputstream=inputstream.adaptive\n")
                    f.write("#KODIPROP:inputstream.adaptive.manifest_type=mpd\n")
                    f.write("#KODIPROP:inputstream.adaptive.license_type=clearkey\n")
                    if api:
                        f.write(f"#KODIPROP:inputstream.adaptive.license_key={api}\n")

                # HLS/M3U8 streams with User-Agent
                elif ".m3u8" in url:
                    f.write("#KODIPROP:inputstream=inputstream.ffmpeg\n")
                    f.write("#KODIPROP:inputstream.adaptive.manifest_type=hls\n")
                    # If the link contains a UA after '|User-Agent=...', extract it
                    if "|User-Agent=" in url:
                        ua = url.split("|User-Agent=")[-1]
                        f.write(f"#EXTVLCOPT:http-user-agent={ua}\n")
                        # Strip UA part from URL
                        url = url.split("|User-Agent=")[0]

                f.write(f"{url}\n")

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
            match_label = f"{event_name}: {teamA} vs {teamB}" if teamA and teamB else event_name
            log.write(f"Event: {match_label}\n")
            for stream in event.get("resolved_streams", []):
                title = stream.get("title", "Unknown Stream")
                url = stream.get("link", "")
                api = stream.get("api", "")
                log.write(f"  {title} -> {url} | license_key={api}\n")
            log.write("\n")

def main():
    data = fetch_json(URL)
    create_m3u(data)
    create_log(data)
    print("stv8.m3u and stv8.log created successfully.")

if __name__ == "__main__":
    main()
