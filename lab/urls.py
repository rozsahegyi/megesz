from django.urls import include, path, re_path
from django.contrib import admin

from . import views

admin.autodiscover()

urlpatterns = [
    path('', views.home, name='home'),
    path('nodes', views.nodes),
    path('status', views.status),
    path('send', views.send),
    path('safe_request', views.safe_request),
    re_path(r'^updates/(?P<id>\w*)$', views.updates),
    re_path(r'^direct/(?P<path>\w+\.(less|css|js))$', views.direct),
]
