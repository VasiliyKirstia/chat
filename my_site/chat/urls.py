from django.conf.urls import url
import chat.views as chat_views

urlpatterns = [
    url(r'^$', chat_views.HomeView.as_view(), name="home"),
    url(r'^init/$', chat_views.init, name="init"),
    url(r'^connect/$', chat_views.connect, name="connect"),
    url(r'^create_conference/$', chat_views.create_conference, name="create_conference"),
    url(r'^send/$', chat_views.send, name="send"),
    url(r'^leave/$', chat_views.leave, name="leave"),
]
