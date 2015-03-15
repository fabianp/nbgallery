# update existing notebooks

from web.models import Notebook
from web.utils import make_screenshots, insert_notebook
import os
import time
import urllib2
import extraction

objs = Notebook.objects.order_by('-accessed_date')
for o in objs:
    p = '/var/www/html/nbgallery/' + o.thumb_img
    try:
        tmp = urllib2.urlopen(o.html_url, timeout=10).read()
        extracted = extraction.Extractor().extract(
            tmp, source_url=o.html_url)
        o.full_html = tmp
        o.save()
    except:
        pass
    #if True: #not os.path.exists(p):
        #print(o.title)
        #out = make_screenshots(o.html_url, o.pk)
        #o.thumb_img = out['thumb']
        #o.save()
        #time.sleep(2) # get some time off
