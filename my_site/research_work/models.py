from django.db import models


class Subject(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.IntegerField(unique=True)


class Pack(models.Model):
    id = models.AutoField(primary_key=True)
    subject = models.ForeignKey(to=Subject, related_name='pack_set')


class KeyPressTime(models.Model):
    id = models.AutoField(primary_key=True)
    key = models.IntegerField()
    time = models.IntegerField()
    pack = models.ForeignKey(to=Pack, related_name='key_press_time_set')


class KeyReleaseTime(models.Model):
    id = models.AutoField(primary_key=True)
    key = models.IntegerField()
    time = models.IntegerField()
    pack = models.ForeignKey(to=Pack, related_name='key_release_time_set')