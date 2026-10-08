# SomaFM Radio — Kodi Audio Addon

Listen to [SomaFM](https://somafm.com), the listener-supported, commercial-free
internet-only radio station broadcasting 40+ hand-picked underground/alternative
channels from San Francisco. No ads, no interruptions — just music chosen by
SomaFM's award-winning DJs.

> This addon is not developed nor endorsed by SomaFM. If you enjoy the music,
> please consider donating at https://somafm.com to keep the service alive.

## What it can do

- **Browse all SomaFM channels** — station name plus the currently playing
  track, artwork, genre, listener count and descriptions, pulled live from
  SomaFM (`channels.json` over HTTPS).
- **Play any station** with one click. Streams are resolved from the
  station's playlist to the fastest Icecast mirror (`ice*.somafm.com`).
- **Quality selector** (`Ask / Auto / Highest MP3 / Lowest MP3 / Highest AAC /
  Lowest AAC`). `Ask` pops up a per-station choice; the rest resolve
  automatically, with sensible fallbacks when a format is unavailable.
- **Sort your way** — by station name, genre or listener popularity, using
  Kodi's sidebar sort button.
- **Station info** — view a channel's description without leaving the list.
- **Song history** — see recently played tracks per station as a clean
  `time – artist – song [album]` list. Times are published in San Francisco
  server time and converted to **your local timezone** automatically
  (stdlib only, no extra dependencies).
- **Song info** context item (`Action(Info)`) for the focused station.
- **Refresh** — clears the listing cache and reloads, so now-playing titles
  update on demand.
- **Function cache with configurable lifetime** — listings are cached locally
  (default 48 hours, adjustable in settings) with a versioned cache, so
  addon updates never serve stale data. Clear it anytime from settings or
  from any station's context menu.

## Requirements

- Kodi 20+ (Nexus or newer, Python 3)
- `script.module.tulip` 4.1.2+
- `script.module.urldispatcher` 1.1.0+
- `script.module.netclient` 1.1.2+
- `script.module.unicache` 1.0.0+

All dependencies resolve automatically when installing from the
Twilight0 repository.

## Installation

1. Add the Twilight0 repository as a source
   (`https://twilight0.github.io/repository/`).
2. Install from repository → Music addons → SomaFM Radio.

## Settings

| Setting | What it does |
|---|---|
| Quality Selector | `Ask` prompts every time; `Auto` picks the highest MP3 (most compatible); the rest pin highest/lowest MP3 or AAC |
| Caching period in hour(s) | How long station listings are kept before refetching (default 48) |
| Clear function cache | Action button: wipes cached listings immediately |

## Notes

- Stream availability and now-playing data come straight from SomaFM's
  servers; if a station is down for them, it's down here too.
- History times are converted from `America/Los_Angeles` to the Kodi
  device's local timezone, including daylight-saving handling.

## License

GPL-3.0-only. See `LICENCES/GPL-3.0-only`.
