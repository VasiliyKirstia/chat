from django.conf.urls import include, url
from django.contrib import admin
import research_work.urls as research_urls
import chat.views as chat_views

urlpatterns = [
    url(r'^$', chat_views.HomeView.as_view(), name="home"),
]
