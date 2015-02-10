from django.db import models


class Notebook(models.Model):
    """
    TODO: prettify
    """
    title = models.CharField(max_length=500)
    text_hash = models.CharField(max_length=100)
    accessed_date = models.DateField(auto_now_add=True)
    thumb_img = models.URLField(max_length=500)
    url = models.URLField(max_length=1000)
    html_url = models.URLField(max_length=1000)
    hits_total = models.IntegerField(default=0)
    description = models.CharField(max_length=2000)

    def __unicode__(self):
        return self.title



class Hit(models.Model):
    created = models.DateTimeField(editable=False)
    ip = models.CharField(max_length=40, editable=False)
    session = models.CharField(max_length=40, editable=False)
    user_agent = models.CharField(max_length=255, editable=False)
    model = models.ForeignKey(Notebook)

