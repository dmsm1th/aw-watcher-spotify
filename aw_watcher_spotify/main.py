#!/usr/bin/env python3

import sys
import logging
import subprocess
import traceback
from typing import Optional
from time import sleep
from datetime import datetime, timezone, timedelta
import argparse

from aw_core import dirs
from aw_core.models import Event
from aw_client.client import ActivityWatchClient
from aw_core.log import setup_logging


DEFAULT_CONFIG = """
[aw-watcher-spotify]
poll_time = 5.0"""

# AppleScript queries the local Spotify desktop app — no API credentials needed.
# Returns pipe-delimited fields or a sentinel string.
_APPLESCRIPT = """
tell application "Spotify"
    if it is running then
        if player state is playing then
            set t to current track
            return (get name of t) & "|||" & (get artist of t) & "|||" & (get album of t) & "|||" & (get spotify url of t)
        else
            return "PAUSED"
        end if
    else
        return "NOT_RUNNING"
    end if
end tell
"""


def get_current_track() -> Optional[dict]:
    try:
        result = subprocess.run(
            ["osascript", "-e", _APPLESCRIPT],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout.strip()
    except subprocess.TimeoutExpired:
        logging.warning("AppleScript timed out querying Spotify")
        return None
    except OSError as exc:
        logging.error("Failed to run osascript: %s", exc)
        return None

    if output in ("NOT_RUNNING", "PAUSED", ""):
        return None

    parts = output.split("|||")
    if len(parts) != 4:
        logging.warning("Unexpected AppleScript output: %r", output)
        return None

    return {
        "title": parts[0],
        "artist": parts[1],
        "album": parts[2],
        "uri": parts[3],
    }


def load_config():
    from aw_core.config import load_config_toml as _load_config

    return _load_config("aw-watcher-spotify", DEFAULT_CONFIG)


def print_statusline(msg):
    last_len = len(print_statusline.last_msg) if hasattr(print_statusline, "last_msg") else 0
    print(" " * last_len, end="\r")
    print(msg, end="\r")
    print_statusline.last_msg = msg


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--testing", action="store_true")
    argparser.add_argument("--verbose", action="store_true")
    args = argparser.parse_args()
    setup_logging(
        name="aw-watcher-spotify",
        testing=args.testing,
        verbose=args.verbose,
        log_stderr=True,
        log_file=True,
    )

    if sys.platform != "darwin":
        logging.error("This watcher uses AppleScript and only runs on macOS.")
        sys.exit(1)

    config = load_config()
    poll_time = float(config["aw-watcher-spotify"].get("poll_time"))

    aw = ActivityWatchClient("aw-watcher-spotify", testing=args.testing)
    bucketname = "{}_{}".format(aw.client_name, aw.client_hostname)
    aw.create_bucket(bucketname, "currently-playing", queued=True)
    aw.connect()

    last_track: Optional[dict] = None
    while True:
        try:
            track = get_current_track()
        except Exception:
            logging.error("Unexpected error fetching track:\n%s", traceback.format_exc())
            sleep(poll_time)
            continue

        try:
            if last_track and (
                not track or track["uri"] != last_track["uri"]
            ):
                print_statusline(
                    "Track ended: {title} - {artist} ({album})\n".format(**last_track)
                )

            if track:
                print_statusline(
                    "Now playing: {title} - {artist} ({album})".format(**track)
                )
                event = Event(timestamp=datetime.now(timezone.utc), data=track)
                aw.heartbeat(bucketname, event, pulsetime=poll_time + 1, queued=True)
            else:
                print_statusline("Waiting for track to start playing...")

            last_track = track
        except Exception:
            logging.error("Unexpected error sending event:\n%s", traceback.format_exc())

        sleep(poll_time)


if __name__ == "__main__":
    main()
