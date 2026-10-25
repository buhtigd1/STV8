import json
import datetime
import requests
from urllib.parse import unquote_plus
from zoneinfo import ZoneInfo

URL = "https://raw.githubusercontent.com/darkbyteprojects/iptv_png/refs/heads/main/provider_2/live_events.json"


def fetch_json(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


def format_event_time(start_str, end_str):
    try:
        start = datetime.datetime.strptime(
            start_str,
            "%Y/%m/%d %H:%M:%S %z"
        ).astimezone(ZoneInfo("Asia/Jakarta"))

        end = datetime.datetime.strptime(
            end_str,
            "%Y/%m/%d %H:%M:%S %z"
        ).astimezone(ZoneInfo("Asia/Jakarta"))

        return f"{start:%H:%M} - {end:%H:%M}"

    except Exception:
        return ""


def get_event_date(start_str):
    try:
        dt = datetime.datetime.strptime(
            start_str,
            "%Y/%m/%d %H:%M:%S %z"
        ).astimezone(ZoneInfo("Asia/Jakarta"))

        return dt.strftime("%d-%m-%Y")

    except Exception:
        return "Unknown-Date"


def write_headers(f, headers):
    headers = headers.replace("&amp;amp;", "&amp;")

    for header in headers.split("&amp;"):

        if "=" not in header:
            continue

        key, value = header.split("=", 1)

        key = key.lower().strip()
        value = unquote_plus(value)

        if key == "user-agent":
            f.write(
                f"#EXTVLCOPT:http-user-agent={value}\n"
            )

        elif key == "referer":
            f.write(
                f"#EXTVLCOPT:http-referrer={value}\n"
            )

        elif key == "origin":
            f.write(
                f"#EXTVLCOPT:http-origin={value}\n"
            )


def create_m3u(data, filename="stv8.m3u"):

    with open(filename, "w", encoding="utf-8") as f:

        f.write('#EXTM3U url-tvg=""\n')
        f.write("\n")    

        for event in data:

            event_info = event.get("eventInfo", {})

            event_name = event_info.get(
                "eventName",
                "Unknown Event"
            )

            teamA = event_info.get("teamA", "")
            teamB = event_info.get("teamB", "")

            logo = event_info.get("eventLogo", "")

            start_time = event_info.get("startTime", "")
            end_time = event_info.get("endTime", "")

            time_label = format_event_time(
                start_time,
                end_time
            )

            group_date = get_event_date(start_time)

            tvg_id = str(event.get("id", ""))

            if teamA and teamB:
                match_label = (
                    f"{event_name}: "
                    f"{teamA} vs {teamB}"
                )
            else:
                match_label = event_name

            if time_label:
                match_label = (
                    f"{time_label} - "
                    f"{match_label}"
                )

            for stream in event.get(
                "resolved_streams",
                []
            ):

                raw_link = stream.get("link", "")

                if not raw_link:
                    continue

                title = stream.get(
                    "title",
                    "Unknown Stream"
                )

                license_key = stream.get(
                    "api",
                    ""
                )

                tvg_name = (
                    f"{match_label} - {title}"
                )

                f.write(
                    f'#EXTINF:-1 '
                    f'tvg-id="{tvg_id}" '
                    f'tvg-name="{tvg_name}" '
                    f'tvg-logo="{logo}" '
                    f'group-title="{group_date}",'
                    f'{tvg_name}\n'
                )

                url = raw_link
                headers = ""

                if "|" in raw_link:
                    url, headers = raw_link.split(
                        "|",
                        1
                    )

                url = url.replace("&amp;amp;", "&amp;")

                is_mpd = ".mpd" in url.lower()
                is_hls = ".m3u8" in url.lower()

                if is_mpd:

                    f.write(
                        "#KODIPROP:inputstream=inputstream.adaptive\n"
                    )

                    f.write(
                        "#KODIPROP:inputstream.adaptive.manifest_type=mpd\n"
                    )

                    f.write(
                        "#KODIPROP:mimetype=application/dash+xml\n"
                    )

                    if license_key:

                        f.write(
                            "#KODIPROP:inputstream.adaptive.license_type=clearkey\n"
                        )

                        f.write(
                            "#KODIPROP:inputstream.adaptive.license_key="
                            f"{license_key}\n"
                        )

                elif is_hls:

                    f.write(
                        "#KODIPROP:inputstream=inputstream.adaptive\n"
                    )

                    f.write(
                        "#KODIPROP:inputstream.adaptive.manifest_type=hls\n"
                    )

                    f.write(
                        "#KODIPROP:mimetype=application/vnd.apple.mpegurl\n"
                    )

                if headers:
                    write_headers(
                        f,
                        headers
                    )

                f.write(url + "\n")


def main():

    try:

        data = fetch_json(URL)

        create_m3u(
            data,
            "stv8.m3u"
        )

        print(
            "stv8.m3u created successfully"
        )

    except Exception as e:

        print(
            f"ERROR: {e}"
        )


if __name__ == "__main__":
    main()
