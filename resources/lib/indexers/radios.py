# -*- coding: utf-8 -*-

"""
    SomaFM Add-on
    Author: Twilight0

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from tulip import directory, client, cache, control, ordereddict
from ..modules import syshandle, sysaddon
from urlparse import urljoin
import json


class Indexer:

    def __init__(self):

        self.list = [] ; self.data = [] ; self.groups = [] ; self.qofs = []
        self.main = 'http://somafm.com'
        self.index = urljoin(self.main, '/listen/genre.html')
        self.switch = {'title': control.lang(30006).format(control.setting('group')),
                       'icon': control.join(control.addonPath, 'resources', 'media', 'selector.png'),
                       'action': 'switcher'}

    def switcher(self):

        def seq(choose):

            control.setSetting('group', choose)
            control.idle()
            control.sleep(50)
            control.refresh()

        self.groups = [control.lang(30003), control.lang(30004), control.lang(30005)]

        choice = control.selectDialog(heading=control.lang(30006), list=self.groups)

        if choice == 0:
            seq(self.groups.pop(0))
        elif choice == 1:
            seq(self.groups.pop(1))
        elif choice == 2:
            seq(self.groups.pop(2))
        else:
            control.execute('Dialog.Close(all)')

    def get_stations(self, url):

        import datetime
        date = datetime.datetime.now()

        html = client.request(url)
        main = client.parseDOM(html, 'div', attrs={'id': 'midstations'})[0]
        items = client.parseDOM(main, 'li')

        for item in items:
            title = client.parseDOM(item, 'h3')[0]
            image = client.parseDOM(item, 'img', ret='src')[0]
            image = urljoin(self.main, image)
            urls = client.parseDOM(item, 'a', ret='href')[3:-1]
            links = [urljoin(self.main, link) for link in urls]
            streams = json.dumps(links)
            listeners = client.parseDOM(item, 'dd')[-2]
            n = client.parseDOM(item, 'span', attrs={'class': 'playing'})[0]
            now = client.parseDOM(n, 'a')[0]
            history = client.parseDOM(n, 'a', ret='href')[0]
            history = urljoin(self.main, history)
            genre = html.split(item)[0]
            genre = client.parseDOM(genre, 'h1', attrs={'class': 'GenreHeader'})[-1]
            description = client.parseDOM(item, 'p', attrs={'class': 'descr'})[0]

            data = {'title': title + ' - ' + now, 'image': image, 'url': streams,
                    'playcount': int(listeners), 'history': history, 'genre': genre, 'artist': now.partition(' - ')[0],
                    'album': title, 'year': date.year, 'lyrics': description}

            self.list.append(data)

        return self.list

    def stations(self):

        import itertools
        from operator import itemgetter

        self.list = cache.get(self.get_stations, 0, self.index)

        if self.list is None:
            return

        for item in self.list:
            item.update({'action': 'play', 'isFolder': 'False'})

        for item in self.list:
            refresh = {'title': 30015, 'query': {'action': 'refresh'}}
            station_info = {'title': 30016, 'query': {'action': 'description', 'text': item['lyrics']}}
            history = {'title': 30017, 'query': {'action': 'history', 'url': item['history']}}
            item.update({'cm': [refresh, station_info, history]})

        if control.setting('group') == control.lang(30003):
            self.list = sorted(self.list, key=lambda k: k['title'].lower())
            self.list = itertools.groupby(self.list, key=itemgetter('title'))
            self.list = [next(item[1]) for item in self.list]
        elif control.setting('group') == control.lang(30004):
            self.list = sorted(self.list, key=lambda k: str(k['playcount']))
            self.list = itertools.groupby(self.list, key=itemgetter('title'))
            self.list = [next(item[1]) for item in self.list]
        elif control.setting('group') == control.lang(30005):
            self.list = sorted(self.list, key=lambda k: k['genre'].lower())
            self.list = itertools.groupby(self.list, key=itemgetter('title'))
            self.list = [next(item[1]) for item in self.list]
        else:
            self.list = self.list

        li = control.item(label=self.switch['title'], iconImage=self.switch['icon'])
        li.setArt({'fanart': control.addonInfo('fanart')})
        url = '{0}?action={1}'.format(sysaddon, self.switch['action'])
        control.addItem(syshandle, url, li)

        directory.add(self.list, infotype='music')
