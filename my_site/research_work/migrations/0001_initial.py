# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='KeyPressTime',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('key', models.IntegerField()),
                ('time', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='KeyReleaseTime',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('key', models.IntegerField()),
                ('time', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Pack',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.IntegerField(unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='pack',
            name='subject',
            field=models.ForeignKey(to='research_work.Subject', related_name='pack_set'),
        ),
        migrations.AddField(
            model_name='keyreleasetime',
            name='pack',
            field=models.ForeignKey(to='research_work.Pack', related_name='key_release_time_set'),
        ),
        migrations.AddField(
            model_name='keypresstime',
            name='pack',
            field=models.ForeignKey(to='research_work.Pack', related_name='key_press_time_set'),
        ),
    ]
