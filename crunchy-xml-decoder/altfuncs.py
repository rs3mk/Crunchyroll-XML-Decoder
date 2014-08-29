import cookielib
import re
import sys
import urlparse
from ConfigParser import ConfigParser

import requests
from ultimate import epnum


def config():
    global video_format
    global resolution
    configr = ConfigParser()
    configr.read('settings.ini')
    quality = configr.get('SETTINGS', 'video_quality')
    qualities = {'android': ['107', '71'], '360p': ['106', '60'], '480p': ['106', '61'],
                 '720p': ['106', '62'], '1080p': ['108', '80'], 'highest': ['0', '0']}
    video_format = qualities[quality][0]
    resolution = qualities[quality][1]
    global lang
    lang = configr.get('SETTINGS', 'language')
    langs = {'Espanol_Espana': 'Espanol (Espana)', 'Francais': 'Francais (France)',
             'Portugues': 'Portugues (Brasil)', 'English': 'English|English (US)'}
    lang = langs[lang]
    return lang


def playerrev(url):
    global player_revision
    try:
        player_revision = re.findall(r'flash\\/(.+)\\/StandardVideoPlayer.swf', gethtml(url)).pop()
    except IndexError:
        url += '?skip_wall=1'  # perv
        html = gethtml(url)
        try:
            player_revision = re.findall(r'flash\\/(.+)\\/StandardVideoPlayer.swf', html).pop()
        except IndexError:
            # Just have something here so it can fail. _start_proxy is what you should use anyway
            player_revision = '20140102185427.932a69b4165d0ca944236b7ca43ae8e5'
    return player_revision


def gethtml(url):
    parts = urlparse.urlsplit(url)
    if not parts.scheme or not parts.netloc:
        print 'Apparently not an URL'
        sys.exit()
    data = {'Referer': 'http://crunchyroll.com/', 'Host': 'www.crunchyroll.com',
            'User-Agent': 'Mozilla/5.0  Windows NT 6.1; rv:26.0 Gecko/20100101 Firefox/26.0'}
    try:
        if 'proxy' in sys.argv:
            proxies = {"http": "127.0.0.1:8118"}
            res = requests.get(url, params=data, proxies=proxies)
        else:
            res = requests.get(url, params=data)
    except IndexError:
        res = requests.get(url, params=data)
    return res.text


def getxml(req, med_id):
    url = 'http://www.crunchyroll.com/xml/'
    if req == 'RpcApiSubtitle_GetXml':
        payload = {'req': 'RpcApiSubtitle_GetXml', 'subtitle_script_id': med_id}
    elif req == 'RpcApiVideoPlayer_GetStandardConfig':
        payload = {'req': 'RpcApiVideoPlayer_GetStandardConfig', 'media_id': med_id, 'video_format': video_format,
                   'video_quality': resolution, 'auto_play': '1', 'show_pop_out_controls': '1',
                   'current_page': 'http://www.crunchyroll.com/'}
    else:
        payload = {'req': req, 'media_id': med_id, 'video_format': video_format, 'video_encode_quality': resolution}
    cookie_jar = cookielib.MozillaCookieJar('cookies.txt').load()
    headers = {'Referer': 'http://static.ak.crunchyroll.com/flash/' + player_revision + '/StandardVideoPlayer.swf',
               'Host': 'www.crunchyroll.com', 'Content-type': 'application/x-www-form-urlencoded',
               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:26.0) Gecko/20100101 Firefox/26.0)'}
    try:
        if 'proxy' in sys.argv:
            proxies = {"http": "127.0.0.1:8118"}
            res = requests.post(url, params=payload, proxies=proxies, cookies=cookie_jar, headers=headers)
        else:
            res = requests.post(url, params=payload, cookies=cookie_jar, headers=headers)
    except IndexError:
        res = requests.post(url, params=payload, cookies=cookie_jar, headers=headers)
    return res.text


def vidurl(url, season, ep):  # experimental, although it does help if you only know the program page.
    res = gethtml(url)
    slist = re.findall('<a href="#" class="season-dropdown content-menu block text-link strong(?: open| ) '
                       'small-margin-bottom" title="(.+?)"', res)
    if slist:  # multiple seasons
        if len(re.findall('<a href=".+episode-(01|1)-(.+?)"', res)) > 1:  # dirty hack, I know
            # print list(reversed(slist))
            # season = int(raw_input('Season number: '))
            # season = sys.argv[3]
            # ep = raw_input('Episode number: ')
            # ep = sys.argv[2]
            season = slist[season]
            return 'http://www.crunchyroll.com/' + re.findall(
                '<a href="(.+episode-0?' + ep + '-(?:.+-)?[0-9]{6})"', res)[slist.index(season)]
        else:
            # print list(reversed(re.findall('<a href=".+episode-(.+?)-',res)))
            # ep = raw_input('Episode number: ')
            # ep = sys.argv[2]
            return 'http://www.crunchyroll.com/' + re.findall('<a href="(.+episode-0?' + ep + '-(?:.+-)?[0-9]{6})"',
                                                              res).pop()
    else:
        # 'http://www.crunchyroll.com/media-'
        # print re.findall('<a href=".+episode-(.+?)-',res)
        # epnum = raw_input('Episode number: ')
        # epnum = sys.argv[2]
        return 'http://www.crunchyroll.com/' + re.findall('<a href="(.+episode-0?' + epnum + '-(?:.+-)?[0-9]{6})"',
                                                          res).pop()