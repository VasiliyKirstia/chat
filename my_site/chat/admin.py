from django.contrib import admin
from chat.models import *

admin.site.register(Conference)
admin.site.register(Message)
admin.site.register(ConferenceUserLink)