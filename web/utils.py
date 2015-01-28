# encoding: utf-8
import os
import urlparse
import urllib2
import socket
import ssl
import requests
import extraction
import base64
import subprocess
from datetime import datetime

from nbviewer.utils import transform_ipynb_uri, ipython_info

from joblib import Memory
#mem = Memory(cachedir='/tmp/joblib2')

from django.conf import settings

#@mem.cache
def urlopen(s):
    return urllib2.urlopen(s, timeout=10).read()




def insert_notebook(url, screenshot=True):
    # TODO: do ajax-based async
    from web.models import Notebook

    # sanitize url
    url = url.replace('https', 'http')

    is_nbviewer = False
    try:
        r = requests.get(url)
        if 'text/html' in r.headers['content-type']:
            # check that it's a notebook
            tmp_html = urlopen(url)
            is_nbviewer = ("Notebook on nbviewer" in tmp_html)
        if is_nbviewer:
            html_url = url
        else:
            html_url = urlparse.urljoin('http://nbviewer.ipython.org', transform_ipynb_uri(url))
        print('Downloading %s' % html_url)
        html = urlopen(html_url)
    except (urllib2.HTTPError, urllib2.URLError, socket.timeout,
            ssl.SSLError, requests.exceptions.SSLError, 
            requests.sessions.InvalidSchema) as e:
        print('Failed in downloading', e)
        return None


    extracted = extraction.Extractor().extract(
        html, source_url=html_url)
    if len(extracted.titles) > 1:
        title = extracted.titles[1]
    else:
        title = extracted.descriptions[1]
    words_title = title.split(' ')
    if len(words_title) > 20:
        title = ' '.join(words_title[:20]) + ' ...'
    if len(extracted.descriptions) > 1:
        description = extracted.descriptions[1]
    else:
        description = ''
    words_description = description.split(' ')
    if len(words_description) > 40:
        description = ' '.join(words_description[:40]) + ' ...'

    # some more sanitation
    if title.startswith('This web site does not host'):
        # this is the nbviewer default title
        title = 'No title'
    title = title.strip(u'¶')


    similar = Notebook.objects.filter(title=title, description=description)
    if len(Notebook.objects.filter(title=title, description=description)) > 0:
        return {'success': False, 'reason': 'Duplicate document', 'link': similar[0].pk}

    obj, created = Notebook.objects.get_or_create(url=url)
    # screenshot
    if screenshot:
        thumb_img = make_screenshots(html_url, obj.pk)
        if thumb_img is None:
            return
        obj.thumb_img = thumb_img

    obj.title = title
    obj.description = description
    obj.html_url = html_url
    obj.url = url
    obj.accessed_date = datetime.now()
    obj.save()
    return {'success': True, 'link' :  obj.pk}


def make_screenshots(url, fname):
    SCREENSHOT_CODE = """
var webshot = require('webshot');

var options = {
  screenSize: {
    width: 1000
  , height: 1000
  }
, shotOffset : { left: 50
    , right: 50
    , top: 50
    , bottom: 0 }
, renderDelay : 1000
, errorIfStatusIsNot200 : true
, customCSS: '#menubar { visibility: hidden} #container { padding-top: -40px}'
}


webshot('%s', '%s', options, function(err) {
  // screenshot now saved
});
"""


    thumb_dir = os.path.join(settings.BASE_DIR, 'static', 'thumb_nb')
    assert os.path.exists(thumb_dir)

    try:
        # first get link and make sure it is accesible
        thumb_fname = os.path.join(thumb_dir, '%s.png' % fname)
        CODE = SCREENSHOT_CODE % (url, thumb_fname)
        jsfile = os.path.join(settings.BASE_DIR, 'screenshot.js')
        with open(jsfile, 'w+') as f:
            f.write(CODE)
        out = subprocess.check_call('nodejs %s' % jsfile, shell=True)
        if out != 0:
            raise ValueError
        print('Screenshot done')
    except KeyboardInterrupt:
        return
    return 'static/thumb_nb/%s.png' % fname


def find_title(html):
    from bs4 import BeautifulSoup
    bs = BeautifulSoup(html)
    titles = bs.find_all('h1')
    if titles:
        t = titles[0].get_text().split(u'\xb6')[0]
        return unicode(t)
    titles2 = bs.find_all('h2')
    if titles2:
        t2 = titles2[0].get_text().split(u'\xb6')[0]
        return unicode(t2)
    else:
        return "No title"



if __name__ == '__main__':
    import os
    os.environ['DJANGO_SETTINGS_MODULE'] = 'nbgallery.settings'
    import sys
    sys.path.append('.')
    import django
    django.setup()
    from web.models import Notebook
    objs = Notebook.objects.order_by('-accessed_date')
    for o in objs:
        print o.url
        insert_notebook(o.url)
