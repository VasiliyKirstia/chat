# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Conference',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='ConferenceUserLink',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('last_message_date', models.IntegerField()),
                ('conference', models.ForeignKey(to='chat.Conference', related_name='users')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='conferences')),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('message', models.TextField()),
                ('time_stamp', models.IntegerField()),
                ('conference', models.ForeignKey(to='chat.Conference', related_name='messages')),
                ('sender', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['time_stamp'],
            },
        ),
        migrations.AddField(
            model_name='conference',
            name='users_set',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='chat.ConferenceUserLink'),
        ),
    ]
