from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(to=User, verbose_name="user profile")
    last_login_data = models.DateTimeField(verbose_name="last login")
