from django.conf.urls import patterns, url
from research_work.views import *

urlpatterns = patterns(
    '',
    url(r'^send_pack/$', send_pack),
)