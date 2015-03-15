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
from PIL import Image
import tempfile

from nbviewer.utils import transform_ipynb_uri, ipython_info

from joblib import Memory
#mem = Memory(cachedir='/tmp/joblib2')

from django.conf import settings

PHANTOMJS_OPTIONS = "--ignore-ssl-errors=true  --ssl-protocol=any --debug=true --web-security=false"

#@mem.cache
def urlopen(s):
    return urllib2.urlopen(s, timeout=10).read()


def unshorten_url(s):
    response = urllib2.urlopen(s) # Some shortened url
    return response.url

def insert_notebook(url, screenshot=True, nb=None):
    """
    Returns
    -------
    dict {'success': True/False}
    """
    # TODO: do ajax-based async
    from web.models import Notebook

    # sanitize url
    url = url.replace('https', 'http')

    is_nbviewer = False
    try:
        url = unshorten_url(url)
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
        if nb is not None:
            nb.failures_access += 1
        print('Failed in downloading', e)
        return {'status': 'failure', 'reason': 'Failed accessing the notebook'}


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


    #similar = Notebook.objects.filter(title=title, description=description)
    #if len(Notebook.objects.filter(title=title, description=description)) > 0:
        #return {'status': 'failure', 'reason': 'duplicate document', 'pk': similar[0].pk}

    if nb is None:
        obj, created = Notebook.objects.get_or_create(url=url)
    else:
        obj = nb
        created = False
    # screenshot
    if screenshot:
        out = make_screenshots(html_url, obj.pk)
        if out['status'] == 'failure':
            if created:
                obj.delete()
            else:
                obj.failures_access += 1
            return out
        else:
            obj.thumb_img = out['thumb']


    # XXX remove assert with error messages
    assert len(title) < 500
    obj.title = title
    assert len(description) < 2000
    obj.description = description
    assert len(html_url) < 1000
    obj.html_url = html_url
    assert len(url) < 1000
    obj.url = url
    obj.full_html = html

    obj.last_accessed_date = datetime.now().date()
    obj.save()
    return {'status': 'success', 'pk' :  obj.pk, 'created': created}


def make_screenshots(url, fname):
    screenshot_js = os.path.join(settings.BASE_DIR, 'web', 'templates', 'screenshot.js')
    SCREENSHOT_CODE = open(screenshot_js).read()

    TMP_DIR = os.path.join(settings.BASE_DIR, 'tmp')
    if not os.path.exists(TMP_DIR):
        os.mkdir(TMP_DIR)

    thumb_dir = os.path.join(settings.BASE_DIR, 'static', 'thumb_nb')
    assert os.path.exists(thumb_dir)
    jsfile = tempfile.NamedTemporaryFile(mode='w+t', suffix='.js', delete=False,
                                         dir=TMP_DIR)
    thumb_tmp = tempfile.NamedTemporaryFile(suffix='.png', dir=TMP_DIR)

    try:
        # first get link and make sure it is accesible
        thumb_fname = os.path.join(thumb_dir, '%s.png' % fname)
        CODE = SCREENSHOT_CODE % (url, thumb_tmp.name)
        jsfile.write(CODE)
        jsfile.flush()
        phantomjs = os.path.join(settings.PHANTOMJS_DIR, 'phantomjs')
        print '%s %s' % (phantomjs, jsfile.name)
        subprocess.call('whoami', shell=True)
        os.chmod(jsfile.name, 0777)
        #subprocess.call('%s %s' % (phantomjs, jsfile.name), shell=True)
        out = subprocess.check_call('%s %s' % (phantomjs, jsfile.name), shell=True)
        if out != 0 or not os.path.exists(thumb_tmp.name):
            return {'status': 'error', 'reason': 'something in phantomjs'}
        img = Image.open(thumb_tmp.name)
        width = img.size[0]
        img = img.crop((width // 2 - 400, 0, width // 2 + 450, 400 + 450))
        img = img.resize((295, 295), Image.ANTIALIAS)
        img.save(thumb_fname)
        # cleanup
    finally:
        jsfile.close()
        thumb_tmp.close()
    return {'status': 'success', 'thumb': 'static/thumb_nb/%s.png' % fname}


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
