aw-watcher-spotify
==================

Watches your currently playing Spotify track and logs it to [ActivityWatch](https://activitywatch.net/).

Forked from [ActivityWatch/aw-watcher-spotify](https://github.com/ActivityWatch/aw-watcher-spotify). The original uses the Spotify Web API and requires OAuth credentials. This fork replaces that with AppleScript, querying the local Spotify desktop app directly — no API keys or login flow needed.

**macOS only.**


## Requirements

- macOS
- [ActivityWatch](https://activitywatch.net/) running locally
- Spotify desktop app (not just the web player)
- Python 3.7+


## Installation

```sh
cd aw-watcher-spotify
pip install .
```


## Running manually

```sh
aw-watcher-spotify
```

Make sure ActivityWatch and the Spotify desktop app are both open first.


## Auto-start on login (recommended)

Create a launchd plist at `~/Library/LaunchAgents/net.activitywatch.aw-watcher-spotify.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>net.activitywatch.aw-watcher-spotify</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/aw-watcher-spotify</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/yourusername/Library/Logs/aw-watcher-spotify.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/yourusername/Library/Logs/aw-watcher-spotify.log</string>
</dict>
</plist>
```

Replace `/path/to/aw-watcher-spotify` with the output of `which aw-watcher-spotify` (or `pyenv which aw-watcher-spotify` if using pyenv).

Then load it:

```sh
launchctl load ~/Library/LaunchAgents/net.activitywatch.aw-watcher-spotify.plist
```


## Configuration

Config is stored in the ActivityWatch config directory (printed on first run).

```toml
[aw-watcher-spotify]
poll_time = 5.0
```

The watcher polls Spotify every `poll_time` seconds. Events within `poll_time + 1` seconds are merged into a continuous session in ActivityWatch.


## Limitations

- macOS only (requires AppleScript and the Spotify desktop app)
- Only tracks playback on the local machine — other devices on your Spotify account are not tracked
- Podcast/episode metadata is limited to what AppleScript exposes
- `popularity` field is not available (was Spotify Web API only)


## Note

You can get a full export of your last year of listening history directly from Spotify at https://www.spotify.com/us/account/privacy/ — useful as a one-time historical import alongside real-time tracking.
