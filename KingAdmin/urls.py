from django.conf.urls import url
from KingAdmin import views

urlpatterns = [
    url(r'^$', views.index, name='table_index'),
    url(r'^index/$', views.index, name='table_index'),
    url(r'^(?P<app_name>\w+)/(?P<table_name>\w+)/$', views.display_table_objs, name='table_objs'),
    url(r'^(?P<app_name>\w+)/(?P<table_name>\w+)/(?P<object_id>\d+)/change/$', views.table_object_change, name='table_object_change'),
    url(r'^(?P<app_name>\w+)/(?P<table_name>\w+)/(?P<object_id>\d+)/delete/$', views.table_object_delete, name='table_object_delete'),
    url(r'^(?P<app_name>\w+)/(?P<table_name>\w+)/add/$', views.table_object_add, name='table_object_add'),
    url(r'^(?P<app_name>\w+)/(?P<table_name>\w+)/(?P<object_id>\d+)/password_reset/$', views.password_reset, name='password_reset'),
]
