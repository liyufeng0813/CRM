from django.conf.urls import url
from student import views

urlpatterns = [
    url(r'^index/', views.index, name='student_index'),
    url(r'^studyrecords/(\d+)/$', views.studyrecords, name='studyrecords'),
    url(r'^homework_detail/(\d+)/$', views.homework_detail, name='homework_detail'),
    url(r'^homework_delete/(\d+)/$', views.homework_delete, name='homework_delete'),
]
