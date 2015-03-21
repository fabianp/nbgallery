from django.conf.urls import patterns, include, url
from django.contrib import admin

import web

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'nbgallery.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    # url(r'^hitcount/$', update_hit_count_ajax, name='hitcount_update_ajax'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', web.views.index, name='index'),
    url(r'^submit/$', web.views.submit, name='submit'),
    url(r'^about/$', web.views.about, name='about'),
    url(r'^redirect/(?P<obj_id>\d+)/$', web.views.nb_redirect, name='redirect'),
    url(r'^sort/(?P<sort_by>\w+)/$', web.views.sort),
    url(r'^sort/(?P<sort_by>\w+)/(?P<obj_id>\d+)/$', web.views.page),
    url(r'^thanks/(?P<obj_id>\d+)/$', web.views.thanks),
    url(r'^list_all/$', web.views.list_all),
)
