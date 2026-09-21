import json
import datetime
import requests
from zoneinfo import ZoneInfo  # Python 3.9+

URL = "https://raw.githubusercontent.com/darkbyteprojects/iptv_png/refs/heads/main/provider_2/live_events.json"

def fetch_json(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def format_event_time(start_str, end_str):
    """Convert UTC timestamps to Jakarta time and format as HH:MM - HH:MM."""
    try:
        if not start_str or not end_str:
            return ""
        start = datetime.datetime.fromisoformat(start_str.replace("Z","")).astimezone(ZoneInfo("Asia/Jakarta"))
        end = datetime.datetime.fromisoformat(end_str.replace("Z","")).astimezone(ZoneInfo("Asia/Jakarta"))
        return f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"
    except Exception:
        return ""

def get_event_date(start_str):
    """Convert UTC timestamp to Jakarta date string (DD-MM-YYYY)."""
    try:
        if start_str:
            start_dt = datetime.datetime.fromisoformat(start_str.replace("Z","")).astimezone(ZoneInfo("Asia/Jakarta"))
            return start_dt.strftime("%d-%m-%Y")
        return "Unknown-Date"
    except Exception:
        return "Unknown-Date"

def create_m3u(data, filename="stv8.m3u"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for event in data:
            event_info = event.get("eventInfo", {})
            event_name = event_info.get("eventName", "Unknown Event")
            logo = event_info.get("eventLogo", "")
            tvg_id = str(event.get("id", ""))

            teamA = event_info.get("teamA", "")
            teamB = event_info.get("teamB", "")

            # Format Jakarta time window
            start_time = event_info.get("startTime", "")
            end_time = event_info.get("endTime", "")
            time_label = format_event_time(start_time, end_time)

            # Date for group-title
            group_date = get_event_date(start_time)

            if teamA and teamB:
                match_label = f"{event_name}: {teamA} vs {teamB}"
            else:
                match_label = event_name

            if time_label:
                match_label = f"{time_label} - {match_label}"

            for stream in event.get("resolved_streams", []):
                title = stream.get("title", "Unknown Stream")
                raw_link = stream.get("link", "")
                api = stream.get("api", "")
                if not raw_link:
                    continue

                tvg_name = f"{match_label} - {title}"
                f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{tvg_name}" tvg-logo="{logo}" group-title="{group_date}",{tvg_name}\n')

                # DASH streams
                if ".mpd" in raw_link:
                    f.write("#KODIPROP:inputstream=inputstream.adaptive\n")
                    f.write("#KODIPROP:inputstream.adaptive.manifest_type=mpd\n")
                    f.write("#KODIPROP:inputstream.adaptive.license_type=clearkey\n")
                    if api:
                        f.write(f"#KODIPROP:inputstream.adaptive.license_key={api}\n")

                # HLS streams
                elif ".m3u8" in raw_link:
                    f.write("#KODIPROP:inputstream=inputstream.ffmpeg\n")
                    f.write("#KODIPROP:inputstream.adaptive.manifest_type=hls\n")

                # Handle extra headers
                url = raw_link
                if "|" in raw_link:
                    url, headers = raw_link.split("|", 1)
                    for header in headers.split("&"):
                        if "=" not in header:
                            continue
                        key, val = header.split("=", 1)
                        key = key.lower()
                        if key == "user-agent":
                            f.write(f"#EXTVLCOPT:http-user-agent={val}\n")
                        elif key == "origin":
                            f.write(f"#EXTVLCOPT:http-origin={val}\n")
                        elif key == "referer":
                            f.write(f"#EXTVLCOPT:http-referrer={val}\n")

                f.write(f"{url}\n")

def create_log(data, filename="stv8.log"):
    with open(filename, "w", encoding="utf-8") as log:
        log.write(f"Generated on: {datetime.datetime.now()}\n")
        total_streams = sum(len(event.get("resolved_streams", [])) for event in data)
        log.write(f"Total events: {len(data)}\n")
        log.write(f"Total streams: {total_streams}\n\n")
        for event in data:
            event_info = event.get("eventInfo", {})
            event_name = event_info.get("eventName", "Unknown Event")
            teamA = event_info.get("teamA", "")
            teamB = event_info.get("teamB", "")
            start_time = event_info.get("startTime", "")
            end_time = event_info.get("endTime", "")
            time_label = format_event_time(start_time, end_time)
            group_date = get_event_date(start_time)

            if teamA and teamB:
                match_label = f"{event_name}: {teamA} vs {teamB}"
            else:
                match_label = event_name

            if time_label:
                match_label = f"{time_label} - {match_label}"

            log.write(f"Event ({group_date}): {match_label}\n")
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
