from django.conf.urls import patterns, url
from research_work.views import HomeView, send_pack

urlpatterns = [
    url(r'^$', HomeView.as_view(), name="home"),
    url(r'^send_pack/$', send_pack),
]