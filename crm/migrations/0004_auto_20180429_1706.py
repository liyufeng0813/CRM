# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-04-29 09:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0003_auto_20180427_1700'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='password',
            field=models.CharField(help_text='<a id="password_reset">点击修改密码</a>', max_length=128, verbose_name='password'),
        ),
    ]
