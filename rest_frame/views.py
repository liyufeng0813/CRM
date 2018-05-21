# !/usr/bin/python3
# -*- coding:utf-8 -*- 

from rest_framework import viewsets

from crm import models
from rest_frame import serialization


class ClassViewSet(viewsets.ModelViewSet):
    queryset = models.ClassList.objects.all()
    serializer_class = serialization.ClassSerializer


class BranchViewSet(viewsets.ModelViewSet):
    queryset = models.Branch.objects.all()
    serializer_class = serialization.BranchSerializer
