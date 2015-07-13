from django.conf.urls import include, url
import auth_system.views as _views

urlpatterns = [
    url(r'^login/$', _views.log_in, name="login"),
    url(r'^logout/$', _views.log_out, name="logout"),
    url(r'^register/$', _views.register, name="register"),
]