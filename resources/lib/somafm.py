# -*- coding: utf-8 -*-

'''
    SomaFM Addon
    Author Twilight0

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
'''

import json
import re
from datetime import datetime
from random import choice

from netclient import Net
from tulip import cleantitle, directory, kodi
from tulip.log import log
from urldispatcher import urldispatcher

from .constants import (
    CHANNELS_JSON, HISTORY_LINK, cache_function, reset_cache,
    stations_cache_duration
)


def _http_json(url):

    try:
        content = Net().http_GET(url).content
        if isinstance(content, bytes):
            content = content.decode('utf-8', 'replace')
        return json.loads(content)
    except Exception as e:
        log('SomaFM: failed to fetch {0}: {1}'.format(url, e))
        return None


def _http_text(url):

    try:
        content = Net().http_GET(url).content
        if isinstance(content, bytes):
            content = content.decode('utf-8', 'replace')
        return content
    except Exception as e:
        log('SomaFM: failed to fetch {0}: {1}'.format(url, e))
        return None


def _strip_tags(html):

    text = re.sub(r'<script.*?</script>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = cleantitle.replaceHTMLCodes(text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    return text.strip()


@cache_function(stations_cache_duration())
def stations_list():

    result = _http_json(CHANNELS_JSON)

    if not isinstance(result, dict):
        return None

    channels = result.get('channels')

    if not channels:
        return None

    year = datetime.now().year
    self_list = []

    for channel in channels:
        try:
            sid = (channel.get('id') or '').strip()
            station = cleantitle.replaceHTMLCodes((channel.get('title') or '').strip()).strip()

            if not sid or not station:
                continue

            description = cleantitle.replaceHTMLCodes((channel.get('description') or '').strip()).strip()
            genre = cleantitle.replaceHTMLCodes((channel.get('genre') or '').strip()).strip() or 'Various'
            image = cleantitle.replaceHTMLCodes((channel.get('largeimage') or channel.get('image') or '').strip())
            fanart = cleantitle.replaceHTMLCodes((channel.get('xlimage') or '').strip())
            try:
                listeners = int(str(channel.get('listeners') or 0).strip())
            except Exception:
                listeners = 0
            now = cleantitle.replaceHTMLCodes((channel.get('lastPlaying') or '').strip()).strip()

            if ' - ' in now:
                artist, song = now.split(' - ', 1)
            else:
                artist, song = '', now

            title = ' - '.join([p for p in (station, song) if p]) or station

            playlists = channel.get('playlists') or []
            # Keep raw playlist urls; quality is resolved at playback time.
            # Stored as JSON string would bloat urls, so play handler re-reads cache.
            urls = [p.get('url') for p in playlists if p.get('url')]
            if not urls:
                continue

            self_list.append(
                {
                    'sid': sid,
                    'title': title,
                    'image': image,
                    'fanart': fanart,
                    'url': sid,
                    'listeners': listeners,
                    'genre': genre,
                    'artist': artist.strip(),
                    'album': station,
                    'year': year,
                    'comment': description,
                    'mediatype': 'music'
                }
            )
        except Exception:
            continue

    return self_list or None


def _by_id(sid):

    for item in stations_list() or []:
        if item.get('sid') == sid or item.get('url') == sid:
            return item
    return None


def _playlists_for(sid):

    result = _http_json(CHANNELS_JSON)

    if not isinstance(result, dict):
        return []

    for channel in result.get('channels') or []:
        if (channel.get('id') or '').strip() == sid:
            return [p for p in (channel.get('playlists') or []) if p.get('url')]

    return []


def _pick_playlist(playlists, mode):

    # mode follows quality_selector setting:
    # 0 Ask, 1 Auto, 2 Highest MP3, 3 Lowest MP3, 4 Highest AAC, 5 Lowest AAC
    def _of(fmt=None, quality=None):
        for p in playlists:
            if fmt and p.get('format') != fmt:
                continue
            if quality and p.get('quality') != quality:
                continue
            return p
        return None

    mp3s = [p for p in playlists if p.get('format') == 'mp3']
    aacs = [p for p in playlists if p.get('format') in ('aac', 'aacp')]

    if mode == '2':
        return _of('mp3', 'highest') or (mp3s[0] if mp3s else None) or (playlists[0] if playlists else None)
    elif mode == '3':
        return _of('mp3', 'low') or (mp3s[-1] if mp3s else None) or (playlists[0] if playlists else None)
    elif mode == '4':
        return _of('aac', 'highest') or _of('aacp', 'high') or (aacs[0] if aacs else None) or (playlists[0] if playlists else None)
    elif mode == '5':
        # Lowest AAC: prefer explicit low, then high, then any AAC.
        # (Old code had this inverted, picking 32k only when 128k existed.)
        return _of('aacp', 'low') or _of('aacp', 'high') or (aacs[-1] if aacs else None) or (playlists[0] if playlists else None)
    else:
        # Auto: highest MP3, the universally compatible default.
        return _of('mp3', 'highest') or (mp3s[0] if mp3s else None) or (playlists[0] if playlists else None)


def _resolve_pls(pls_url):

    text = _http_text(pls_url)

    if not text:
        return None

    files = re.findall(r'(?im)^File\d+=(.+?)\s*$', text)

    if not files:
        return None

    return choice(files).strip()


@urldispatcher.register('root')
def root():

    self_list = stations_list()

    if not self_list:
        kodi.infoDialog(kodi.i18n(30021))
        return

    self_list = sorted(self_list, key=lambda k: k['album'].lower())

    for item in self_list:
        sid = item.pop('sid', item.get('url'))
        item['url'] = sid

        refresh = {'title': 30015, 'query': {'action': 'refresh'}}
        cache_clear = {'title': 30002, 'query': {'action': 'clear_cache'}}
        station_info = {'title': 30016, 'query': {'action': 'description', 'url': sid}}
        history = {'title': 30017, 'query': {'action': 'history', 'url': sid}}
        info_cm = {'title': 30020, 'query': {'action': 'info'}}

        item.update(
            {
                'cm': [refresh, cache_clear, history, station_info, info_cm],
                'action': 'play', 'isFolder': 'False', 'isPlayable': 'True'
            }
        )

    for count, item in enumerate(self_list, start=1):
        item.setdefault('tracknumber', count)

    kodi.setsortmethod('album')
    kodi.setsortmethod('genre')
    kodi.setsortmethod('listeners')

    directory.builder(self_list, content='songs', infotype='music')


@urldispatcher.register('play', kwargs=['url'])
def play(url):

    sid = url
    item = _by_id(sid) or {'album': sid, 'title': sid, 'image': ''}
    playlists = _playlists_for(sid)

    if not playlists:
        kodi.infoDialog(kodi.i18n(30021))
        _resolve_fail()
        return

    try:
        mode = kodi.setting('quality_selector') or '1'
    except Exception:
        mode = '1'

    if mode == '0':
        labels = []
        for p in playlists:
            fmt = (p.get('format') or '').upper()
            quality = (p.get('quality') or '').capitalize()
            labels.append('{0} {1}'.format(fmt, quality).strip() or p.get('url'))

        try:
            picked = kodi.selectDialog(labels, heading=kodi.i18n(30007))
        except Exception:
            picked = -1

        if picked is None or picked == -1 or picked >= len(playlists):
            _resolve_fail()
            return

        pls_url = playlists[picked].get('url')
    else:
        chosen = _pick_playlist(playlists, mode)
        pls_url = (chosen or {}).get('url')

    if not pls_url:
        kodi.infoDialog(kodi.i18n(30021))
        _resolve_fail()
        return

    stream = _resolve_pls(pls_url)

    if not stream:
        kodi.infoDialog(kodi.i18n(30021))
        _resolve_fail()
        return

    # Title-only meta like E-Radio: artist/album as strings crash
    # setInfo on Kodi 21+ ("artist needs a list of strings").
    directory.resolve(stream, {'title': item.get('title', sid)}, item.get('image', ''))


def _resolve_fail():

    # Tell the playlist player this item failed instead of leaving it
    # hanging (which makes "Play from here" walk the whole station list).
    try:
        from tulip.init import syshandle
        kodi.resolve(syshandle, False, kodi.item())
    except Exception as e:
        log('SomaFM: failed to signal resolve failure: {0}'.format(e))


@urldispatcher.register('description', kwargs=['url', 'text'])
def description(url, text=None):

    # Pre-4.0 context items passed ?action=description&text=<comment>.
    # Accept both: sid lookup first, legacy raw text as fallback.
    if text and not _by_id(url):
        kodi.text_viewer('SomaFM', text or '-')
        return

    item = _by_id(url)
    text = (item or {}).get('comment') or text or ''
    kodi.text_viewer('SomaFM', text or '-')


def _cell(text):

    text = re.sub(r'<[^>]+>', '', text or '')
    text = cleantitle.replaceHTMLCodes(text)
    text = text.replace('\xa0', ' ').strip()
    return re.sub(r'\s+', ' ', text)


def _sf_wall_to_local(raw):
    # Server times are San Francisco wall clock (America/Los_Angeles,
    # PDT UTC-7 / PST UTC-8). Convert to the device's local timezone so
    # every user sees correct times. Stdlib only: zoneinfo when tzdata
    # exists, otherwise manual US-DST rules. Returns converted string,
    # preserving the "(Now)" marker; falls back to raw on any failure.
    import time as _time
    from datetime import datetime, timedelta, timezone

    m = re.match(r'\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(\(Now\))?\s*', raw or '')
    if not m:
        return raw

    hour, minute, second, now_mark = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0), m.group(4) or ''

    try:
        from zoneinfo import ZoneInfo
        sf_tz = ZoneInfo('America/Los_Angeles')
        utc_now = datetime.now(timezone.utc)
        sf_now = utc_now.astimezone(sf_tz)
        sf_dt = sf_now.replace(hour=hour, minute=minute, second=second, microsecond=0)
        # Songs list spans ~2h; a wall time >1h in the future means yesterday.
        if (sf_dt - sf_now).total_seconds() > 3600:
            sf_dt -= timedelta(days=1)
        local_dt = sf_dt.astimezone()
        out = local_dt.strftime('%H:%M:%S')
        return out + (' ' + now_mark if now_mark else '')
    except Exception:
        pass

    try:
        # Fallback without tzdata: US DST = 2nd Sun Mar 02:00 -> 1st Sun Nov 02:00 local.
        def _nth_sunday(year, month, n):
            from datetime import date
            d = date(year, month, 1)
            offset = (6 - d.weekday()) % 7
            return d.fromordinal(d.toordinal() + offset + 7 * (n - 1))

        utc_now = datetime.now(timezone.utc)
        # Determine SF offset from UTC-based boundaries (10:00 UTC Mar / 09:00 UTC Nov).
        y = utc_now.year
        start = datetime(y, 3, _nth_sunday(y, 3, 2).day, 10, tzinfo=timezone.utc)
        end = datetime(y, 11, _nth_sunday(y, 11, 1).day, 9, tzinfo=timezone.utc)
        sf_offset = -7 if start <= utc_now < end else -8
        sf_today = (utc_now + timedelta(hours=sf_offset)).date()
        wall = datetime(sf_today.year, sf_today.month, sf_today.day, hour, minute, second)
        utc_instant = (wall - timedelta(hours=sf_offset)).replace(tzinfo=timezone.utc)
        # Midnight rollover guard: wall time >1h in the future means yesterday.
        if utc_instant - utc_now > timedelta(hours=1):
            utc_instant -= timedelta(days=1)
        local_dt = utc_instant.astimezone()
        out = local_dt.strftime('%H:%M:%S')
        return out + (' ' + now_mark if now_mark else '')
    except Exception:
        return raw


@urldispatcher.register('history', kwargs=['url'])
def history(url):

    html = _http_text(HISTORY_LINK.format(url))

    if not html:
        kodi.text_viewer('SomaFM', '-')
        return

    block = re.search(r'''(?is)<div[^>]*\bid\s*=\s*['"]playinc['"][^>]*>(.*?)</table>''', html)
    table = block.group(1) if block else html
    rows = re.findall(r'(?is)<tr[^>]*>(.*?)</tr>', table)

    lines = []
    for row in rows:
        cols = re.findall(r'(?is)<td[^>]*>(.*?)</td>', row)
        if len(cols) < 3:
            continue
        played, artist, song = (_cell(c) for c in cols[:3])
        album = _cell(cols[3]) if len(cols) > 3 else ''

        if 'Played At' in played and 'Artist' in artist:
            continue
        if 'Break / Station ID' in row or 'Break / Station ID' in artist:
            continue
        if not artist and not song:
            continue

        if album:
            lines.append('{0} - {1} - {2} [{3}]'.format(_sf_wall_to_local(played), artist, song, album).strip(' -'))
        else:
            lines.append('{0} - {1} - {2}'.format(_sf_wall_to_local(played), artist, song).strip(' -'))

    if not lines:
        # Markup drift: fall back to stripped block instead of whole page.
        text = _strip_tags(table)
        kodi.text_viewer('SomaFM', text or '-')
        return

    item = _by_id(url)
    station = (item or {}).get('album') or url
    header = '{0} - Recently Played (your local time)'.format(station)
    kodi.text_viewer('SomaFM', header + '\n\n' + '\n'.join(lines))


@urldispatcher.register('info')
def info_cm():

    kodi.execute('Action(Info)')


# Backward-compat aliases for pre-4.0 favourites / settings:
# old names were cache_clear (settings action) -> clear_cache handler
# is now 'clear_cache', and info_cm -> 'info'.
@urldispatcher.register('cache_clear')
def _alias_cache_clear():

    return cache_clear()


@urldispatcher.register('info_cm')
def _alias_info_cm():

    return info_cm()


@urldispatcher.register('clear_cache')
def cache_clear():

    try:
        ok = bool(reset_cache())
    except Exception as e:
        log('SomaFM: cache clear failed: {0}'.format(e))
        ok = False

    kodi.infoDialog(kodi.i18n(30402) if ok else kodi.i18n(30021))
    kodi.refresh()


@urldispatcher.register('refresh')
def refresh():

    # Refresh means fresh data: drop the listing cache, then re-enter
    # the container. Silent on purpose (clear_cache already covers
    # the explicit "tell me it worked" case).
    try:
        reset_cache()
    except Exception as e:
        log('SomaFM: refresh cache clear failed: {0}'.format(e))

    kodi.refresh()
