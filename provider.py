import datetime
import requests
import unicodedata

from html import unescape
from urllib.parse import (
    unquote_plus,
    urlparse,
)
from zoneinfo import ZoneInfo

URL = (
    "https://raw.githubusercontent.com/"
    "darkbyteprojects/iptv_png/"
    "refs/heads/main/provider_2/live_events.json"
)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/141.0.0.0 Safari/537.36 "
    "Edg/141.0.0.0"
)


def fetch_json(url):

    r = requests.get(
        url,
        timeout=30
    )

    r.raise_for_status()

    r.encoding = "utf-8"

    return r.json()


def fix_text(text):
    """
    Perbaiki mojibake:
    KÃ¶ln -> Köln
    AtlÃ©tico -> Atlético
    SÃ©rie -> Série
    """

    if not isinstance(text, str):
        return text

    try:

        if any(
            bad in text
            for bad in (
                "Ã",
                "Â",
                "â€",
                "â€™",
                "â€œ",
                "â€\x9d",
                "â€“",
                "â€”",
            )
        ):

            text = (
                text.encode("latin1")
                .decode("utf-8")
            )

    except Exception:
        pass

    return unicodedata.normalize(
        "NFC",
        text
    )


def fix_json_text(obj):

    if isinstance(obj, dict):

        return {
            k: fix_json_text(v)
            for k, v in obj.items()
        }

    if isinstance(obj, list):

        return [
            fix_json_text(x)
            for x in obj
        ]

    if isinstance(obj, str):
        return fix_text(obj)

    return obj


def format_event_time(
    start_str,
    end_str
):

    try:

        start = (
            datetime.datetime.strptime(
                start_str,
                "%Y/%m/%d %H:%M:%S %z"
            )
            .astimezone(
                ZoneInfo("Asia/Jakarta")
            )
        )

        end = (
            datetime.datetime.strptime(
                end_str,
                "%Y/%m/%d %H:%M:%S %z"
            )
            .astimezone(
                ZoneInfo("Asia/Jakarta")
            )
        )

        return (
            f"{start:%H:%M}"
            f" - "
            f"{end:%H:%M}"
        )

    except Exception:
        return ""


def get_event_date(start_str):

    try:

        dt = (
            datetime.datetime.strptime(
                start_str,
                "%Y/%m/%d %H:%M:%S %z"
            )
            .astimezone(
                ZoneInfo("Asia/Jakarta")
            )
        )

        return dt.strftime(
            "%d-%m-%Y"
        )

    except Exception:
        return "Unknown-Date"


def sort_events(events):

    def get_sort_key(event):

        try:

            start_time = (
                event
                .get(
                    "eventInfo",
                    {}
                )
                .get(
                    "startTime",
                    ""
                )
            )

            return (
                datetime.datetime.strptime(
                    start_time,
                    "%Y/%m/%d %H:%M:%S %z"
                )
                .astimezone(
                    ZoneInfo(
                        "Asia/Jakarta"
                    )
                )
            )

        except Exception:

            return (
                datetime.datetime.max
            )

    return sorted(
        events,
        key=get_sort_key
    )


def write_headers(
    f,
    headers
):

    headers = unescape(
        headers
    )

    for sep in (
        "&amp;amp;amp;amp;",
        "&amp;amp;amp;",
        "&amp;amp;",
        "&amp;",
        "&"
    ):
        headers = headers.replace(
            sep,
            "|"
        )

    found_user_agent = False

    for header in headers.split(
        "|"
    ):

        if "=" not in header:
            continue

        key, value = header.split(
            "=",
            1
        )

        key = (
            key
            .strip()
            .lower()
        )

        value = unquote_plus(
            value.strip()
        )

        if not value:
            continue

        if key == "user-agent":

            found_user_agent = True

            f.write(
                "#EXTVLCOPT:"
                f"http-user-agent={value}\n"
            )

        elif key in (
            "referer",
            "referrer"
        ):

            f.write(
                "#EXTVLCOPT:"
                f"http-referrer={value}\n"
            )

        elif key == "origin":

            f.write(
                "#EXTVLCOPT:"
                f"http-origin={value}\n"
            )

    return found_user_agent


def create_m3u(
    data,
    filename="stv8.m3u"
):

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            '#EXTM3U url-tvg=""\n\n'
        )

        for event in data:

            event_info = event.get(
                "eventInfo",
                {}
            )

            event_name = event_info.get(
                "eventName",
                "Unknown Event"
            )

            teamA = event_info.get(
                "teamA",
                ""
            )

            teamB = event_info.get(
                "teamB",
                ""
            )

            logo = event_info.get(
                "eventLogo",
                ""
            )

            start_time = event_info.get(
                "startTime",
                ""
            )

            end_time = event_info.get(
                "endTime",
                ""
            )

            time_label = (
                format_event_time(
                    start_time,
                    end_time
                )
            )

            group_date = (
                get_event_date(
                    start_time
                )
            )

            if teamA and teamB:

                match_label = (
                    f"{event_name}: "
                    f"{teamA} vs {teamB}"
                )

            else:

                match_label = (
                    event_name
                )

            if time_label:

                match_label = (
                    f"{time_label} - "
                    f"{match_label}"
                )

            for stream in event.get(
                "resolved_streams",
                []
            ):

                raw_link = stream.get(
                    "link",
                    ""
                )

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

                channel_name = (
                    f"{match_label}"
                    f" - "
                    f"{title}"
                )

                kodi_id = event.get(
                    "id",
                    ""
                )

                f.write(
                    f'#EXTINF:-1 '
                    f'tvg-id="{kodi_id}" '
                    f'tvg-logo="{logo}" '
                    f'group-title="{group_date}",'
                    f'{channel_name}\n'
                )

                url = raw_link
                headers = ""

                if "|" in raw_link:

                    url, headers = (
                        raw_link.split(
                            "|",
                            1
                        )
                    )

                url = (
                    unescape(url)
                    .strip()
                )

                path = (
                    urlparse(url)
                    .path
                    .lower()
                )

                is_mpd = (
                    ".mpd" in path
                )

                is_hls = (
                    ".m3u8" in path
                )

                if is_mpd:

                    f.write(
                        "#KODIPROP:"
                        "inputstream="
                        "inputstream.adaptive\n"
                    )

                    f.write(
                        "#KODIPROP:"
                        "inputstream.adaptive."
                        "manifest_type=mpd\n"
                    )

                    if license_key:

                        f.write(
                            "#KODIPROP:"
                            "inputstream.adaptive."
                            "license_type=clearkey\n"
                        )

                        f.write(
                            "#KODIPROP:"
                            "inputstream.adaptive."
                            "license_key="
                            f"{license_key}\n"
                        )

                elif is_hls:

                    f.write(
                        "#KODIPROP:"
                        "inputstream="
                        "inputstream.adaptive\n"
                    )

                    f.write(
                        "#KODIPROP:"
                        "inputstream.adaptive."
                        "manifest_type=hls\n"
                    )

                found_user_agent = False

                if headers:

                    found_user_agent = (
                        write_headers(
                            f,
                            headers
                        )
                    )

                if not found_user_agent:

                    f.write(
                        "#EXTVLCOPT:"
                        f"http-user-agent="
                        f"{DEFAULT_USER_AGENT}\n"
                    )

                f.write(
                    url + "\n\n"
                )


def main():

    try:

        data = fetch_json(
            URL
        )

        data = fix_json_text(
            data
        )

        data = sort_events(
            data
        )

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
