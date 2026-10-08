# -*- coding: utf-8 -*-

'''
    SomaFM Addon
    Author Twilight0

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
'''

from sys import argv
from urllib.parse import parse_qsl

from urldispatcher import urldispatcher

from resources.lib import somafm  # noqa: F401
from tulip.log import log


def main(argv=argv):

    try:
        params = dict(parse_qsl(argv[2][1:]))
    except IndexError:
        params = {}

    action = params.get('action') or 'root'

    try:
        urldispatcher.dispatch(action, params)
    except Exception as e:
        # Stale actions (e.g. pre-4.0 favourites using info_cm/cache_clear
        # or description?text=...) must not kill the listing when the
        # interpreter is reused across invocations.
        log('SomaFM: action |{0}| failed ({1})'.format(action, e))
        if action == 'play':
            # A directory listing here would make the playlist player walk
            # every station as "unplayable". Signal failure instead.
            try:
                from tulip import kodi as _kodi
                handle = int(argv[1])
                _kodi.resolve(handle, False, _kodi.item())
            except Exception:
                pass
        elif action != 'root':
            try:
                urldispatcher.dispatch('root', {})
            except Exception:
                pass


if __name__ == '__main__':

    main()
