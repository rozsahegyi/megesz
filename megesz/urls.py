from django.urls import include, path
from django.contrib import admin

from lab import views

admin.autodiscover()

urlpatterns = [
    path('', views.home, name='home'),
    path('lab/', include('lab.urls')),
    path('admin/', admin.site.urls),
]
