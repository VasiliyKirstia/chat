from django.db import models
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.utils.html import escape


class Conference(models.Model):
    id = models.AutoField(primary_key=True)

    users_set = models.ManyToManyField(to=User, through='ConferenceUserLink')

    def get_members_names(self, user):
        return [_user.username for _user in self.users_set.all().exclude(pk=user.pk)]

    def get_members_names_with_status(self):
        active_uid_list = []
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        links = ConferenceUserLink.objects.filter(conference=self)

        for session in sessions:
            data = session.get_decoded()
            active_uid_list.append(data.get('_auth_user_id', None))
        return [[link.user.username, True if link.user.pk in active_uid_list else False] for link in links]

    def get_new_messages(self, user):
        last_message_time_stamp = ConferenceUserLink.objects.get(conference=self, user=user).last_message_date
        new_messages = Message.objects.filter(conference=self, time_stamp__gt=last_message_time_stamp)
        return new_messages

    def get_new_messages_count(self, user):
        last_message_time_stamp = ConferenceUserLink.objects.get(conference=self, user=user).last_message_date
        new_messages_count = Message.objects.filter(conference=self, time_stamp__gt=last_message_time_stamp).count()
        return new_messages_count

    def get_messages_younger_then(self, time_stamp):
        return Message.objects.filter(conference=self, time_stamp__gt=time_stamp)

    def leave(self, user):
        for_remove = ConferenceUserLink.objects.get(conference=self, user=user)
        if for_remove is not None:
            for_remove.delete()
        if self.users_set.count() == 0:
            self.delete()

    def add_message(self, sender, message):
        Message.objects.create(conference=self,
                               sender=sender,
                               message=escape(message),
                               time_stamp=timezone.now().timestamp())


class ConferenceUserLink(models.Model):
    id = models.AutoField(primary_key=True)

    user = models.ForeignKey(to=User, related_name='conferences')

    conference = models.ForeignKey(to=Conference, related_name='users')

    last_message_date = models.IntegerField()


class Message(models.Model):
    id = models.AutoField(primary_key=True)

    message = models.TextField()

    conference = models.ForeignKey(to=Conference, related_name='messages')

    sender = models.ForeignKey(to=User)

    time_stamp = models.IntegerField()

    class Meta:
        ordering = ['time_stamp']