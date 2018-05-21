# !/usr/bin/python3
# -*- coding:utf-8 -*- 

from django.conf.urls import url, include
from rest_framework import routers

from rest_frame import views


router = routers.DefaultRouter()
router.register(r'class', views.ClassViewSet)
router.register(r'teacher', views.BranchViewSet)


urlpatterns = [
    url(r'', include(router.urls)),
]
