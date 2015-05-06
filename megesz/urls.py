from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'lab.views.home', name='home'),
    url(r'^lab/', include('lab.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
