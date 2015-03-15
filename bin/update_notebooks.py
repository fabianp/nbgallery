# update existing notebooks

from web.models import Notebook
from web.utils import make_screenshots, insert_notebook
import os
import time
import urllib2
import extraction
import datetime

# local imports
from web import utils

today = datetime.datetime.now().date()
last_week = today - datetime.timedelta(days=5)

objs = Notebook.objects.filter(accessed_date__lt=last_week)
for o in objs:
    out = utils.insert_notebook(o.url, nb=o)
    print('Finished: %s' % out)
