from django.conf.urls import url
from crm import views

urlpatterns = [
    url(r'^index/', views.index, name='sales_index'),
    url(r'^customer_list/', views.customer_list, name='customer_list'),
    url(r'^customer/(?P<object_id>\d+)/enrollment/', views.enrollment, name='enrollment'),
    url(r'^customer/registration/(?P<enrollment_id>\d+)/(?P<random_str>\w+)', views.student_registration, name='student_regitration'),
    url(r'^customer/registration_check/(?P<enrollment_id>\d+)/', views.registration_check, name='registration_check'),
    url(r'^customer/registration_reject/(?P<enrollment_id>\d+)/', views.registration_reject, name='registration_reject'),
    url(r'^customer/registration_payment/(?P<enrollment_id>\d+)/', views.registration_payment, name='registration_payment'),
]
