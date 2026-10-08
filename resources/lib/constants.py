# -*- coding: utf-8 -*-

'''
    SomaFM Addon
    Author Twilight0

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
'''

from tulip.kodi import cacheDirectory, join
from pickled import FunctionCache

# Bump whenever fetch/parse logic changes so stale cached listings
# can never be served after an update.
CACHE_VERSION = 'v3'

_cache_path = join(cacheDirectory, CACHE_VERSION)

cache_function = FunctionCache(_cache_path).cache_function
reset_cache = FunctionCache(_cache_path).reset_cache

BASE_LINK = 'https://somafm.com'
CHANNELS_JSON = ''.join([BASE_LINK, '/channels.json'])
HISTORY_LINK = ''.join([BASE_LINK, '/{0}/songhistory.html'])


def cache_duration(minutes):
    from tulip import kodi
    try:
        if kodi.setting('debug') == 'true':
            return 0
    except Exception:
        pass
    return minutes


def stations_cache_duration():
    from tulip import kodi
    try:
        hours = int(kodi.setting('period') or 48)
    except Exception:
        hours = 48
    if hours <= 0:
        return 0
    return cache_duration(hours * 60)
