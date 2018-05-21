# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-04-26 16:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='role',
            options={'verbose_name_plural': '用户类型表'},
        ),
        migrations.AddField(
            model_name='userprofile',
            name='roles',
            field=models.ManyToManyField(to='crm.Role', verbose_name='用户类型'),
        ),
    ]
