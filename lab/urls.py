from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'lab.views.home', name='home'),
    url(r'^nodes$', 'lab.views.nodes'),
    url(r'^status$', 'lab.views.status'),
    url(r'^send$', 'lab.views.send'),
    url(r'^safe_request$', 'lab.views.safe_request'),
    url(r'^updates/(?P<id>\w*)$', 'lab.views.updates'),
    url(r'^direct/(?P<path>\w+\.(less|css|js))$', 'lab.views.direct'),
)
