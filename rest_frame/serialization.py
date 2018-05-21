# !/usr/bin/python3
# -*- coding:utf-8 -*-

from rest_framework import serializers

from crm import models


class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ClassList
        depth = 2
        fields = ('class_type', 'course', 'branch')


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Branch
        fields = ('name', 'addr')
