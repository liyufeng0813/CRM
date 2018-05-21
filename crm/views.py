import os

from django.shortcuts import render, redirect, HttpResponse
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.contrib.auth.decorators import login_required

from PerfectCRM.settings import ENROLLED_IMAGE_PATH
from crm import forms, models, utils


@login_required
def index(request):
    return render(request, 'index.html')


@login_required
def customer_list(request):
    return render(request, 'sales/customers.html')


@login_required
def enrollment(request, object_id):
    """
    提交的报名表有三种状态：
    1.这条报名信息已经存在了，且客户已经同意了合同，直接return；
    2.这条报名信息已经存在了，但是客户还没有同意报名合同，再返回一个合同链接给客户；
    3.这条报名信息不存在，创建报名信息。
    """
    enrollment_modelform = forms.EnrollmentModelForm()
    customer_object = models.Customer.objects.filter(id=object_id)[0]
    message = {}
    if request.method == 'POST':

        enrollment_obj = models.Enrollment.objects.filter(customer_id=object_id,
                                                          enrolled_class_id=request.POST['enrolled_class'])
        # 如果这个用户已经报名了这个课程且同意了合同。
        if enrollment_obj and enrollment_obj[0].contract_agreed:
            message['agreed'] = '这个用户已经报名这个课程，且同意了合同。'
            return render(request, 'sales/enrollment.html', {'enrollment_modelform': enrollment_modelform,
                                                             'customer_object': customer_object,
                                                             'message': message})

        enrollment_modelform = forms.EnrollmentModelForm(request.POST)
        if enrollment_modelform.is_valid():
            try:
                # 尝试创建报名信息，如果引发联合唯一错误，说明这条报名已经存在；没有错误则创建。
                enrollment_modelform.cleaned_data['customer_id'] = object_id
                enrollment_object = models.Enrollment.objects.create(**enrollment_modelform.cleaned_data)
                # 用户的报名链接加上一个随机值，并且进行缓存处理，如果超过两个小时，这个链接失效。
                random_str = utils.get_random_str()
                cache.set(enrollment_object.id, random_str, 60*60*2)
                message['customer_enrollment_link'] = \
                    'http://127.0.0.1:8000/crm/customer/registration/{}/{}'.format(enrollment_object.id, random_str)
            except IntegrityError:
                # 捕获联合唯一错误，说明报名信息已经存在，再放回一个合同链接给客户。
                random_str = utils.get_random_str()
                cache.set(enrollment_obj[0].id, random_str, 7200)
                message['customer_enrollment_link'] = \
                    'http://127.0.0.1:8000/crm/customer/registration/{}/{}'.format(enrollment_obj[0].id, random_str)
    return render(request, 'sales/enrollment.html', {'enrollment_modelform': enrollment_modelform,
                                                     'customer_object': customer_object,
                                                     'message': message})


@login_required
def student_registration(request, enrollment_id, random_str):
    """
    学员报名
        判断报名链接中的随机字符串和缓存中的随机字符串是否相等；
            不相等：
                提示连接失效，返回。
        POST请求方式：
            ajax方式：
                保存用户提交的图片。
            判断用户是否已经报名，如果已经报名，提示已经报名，返回；
            表单提交方式：
                保存报名表的信息；
                报名表设置为已报名。
    """
    if random_str != cache.get(enrollment_id):
        # 如果这个报名表的用户报名链接的随机值和缓存中的值进行比较，不相同则链接过期了。
        return HttpResponse('<h1>此链接已失效，请再次申请。</h1>')
    try:
        enrollment_object = models.Enrollment.objects.get(id=enrollment_id)
    except ObjectDoesNotExist:
        return HttpResponse('<h1>go away</h1>')
    registration_modelform = forms.StudentRegistrationModelForm(instance=enrollment_object.customer)
    message = {}
    if request.method == 'POST':
        if request.is_ajax():
            """如果是 ajax 方式，则是图片上传，保存图片。"""
            file = request.FILES.get('file')
            enrolled_image_path = os.path.join(ENROLLED_IMAGE_PATH, enrollment_id)
            if not os.path.exists(enrolled_image_path):
                os.makedirs(enrolled_image_path, exist_ok=True)
            with open('{}/{}'.format(enrolled_image_path, file.name), 'wb') as f:
                for chunk in file.chunks():
                    f.write(chunk)
            return HttpResponse('succes')

        if enrollment_object.contract_agreed:
            message['agreed'] = '您已经报名，请不要重复报名。'
            return render(request, 'sales/student_registration.html', {'registration_modelform': registration_modelform,
                                                                       'enrollment_object': enrollment_object,
                                                                       'message': message})
        registration_modelform = forms.StudentRegistrationModelForm(request.POST, instance=enrollment_object.customer)
        if registration_modelform.is_valid():
            registration_modelform.save()
            enrollment_object.contract_agreed = True
            enrollment_object.save()
            message['agreed'] = '您已报名成功，请耐心等待审核。'
            return redirect('/crm/customer/registration_check/{}/'.format(enrollment_id))
    return render(request, 'sales/student_registration.html', {'registration_modelform': registration_modelform,
                                                               'enrollment_object': enrollment_object,
                                                               'message': message})


@login_required
def registration_check(request, enrollment_id):
    """
    对报名表进行审核
    """
    enrollment_object = models.Enrollment.objects.get(id=enrollment_id)
    customer_object = enrollment_object.customer
    if request.method == 'GET':
        enrollment_modelform = forms.EnrollmentModelForm(instance=enrollment_object)
        customer_modelform = forms.StudentRegistrationModelForm(instance=customer_object)
        return render(request, 'sales/registration_check.html', {'enrollment_modelform': enrollment_modelform,
                                                                 'customer_modelform': customer_modelform,
                                                                 'enrollment_id': enrollment_id})


@login_required
def registration_reject(request, enrollment_id):
    """
    报名表审核不通过时：
        把客户的报名表的已报名字段重置为False；
        跳转到客户报名页面。
    """
    enrollment_object = models.Enrollment.objects.get(id=enrollment_id)
    enrollment_object.contract_agreed = False
    enrollment_object.save()
    return redirect('/crm/customer/{}/enrollment/'.format(enrollment_object.customer.id))


@login_required
def registration_payment(request, enrollment_id):
    """
    报名表审核通过时：
        跳到缴费页面；
        输入的已缴费用有三种可能：
            1 输入的不是数字；
            2 输入费用小于500，最小500；
            3 输入大于500，成功缴费：
                创建一条客户的缴费记录；
                把报名表内的审核设置为True；
                把客户的客户表设置为已报名。
    """
    enrollment_object = models.Enrollment.objects.get(id=enrollment_id)
    customer_object = enrollment_object.customer
    errors = []
    if request.method == 'GET':
        return render(request, 'sales/registration_payment.html', {'enrollment_object': enrollment_object,
                                                                   'customer_object': customer_object,
                                                                   'errors': errors})
    elif request.method == 'POST':
        try:
            amount = int(request.POST.get('amount', 0))
        except ValueError:
            errors.append('已缴费用：只能为数字！')
            return render(request, 'sales/registration_payment.html', {'enrollment_object': enrollment_object,
                                                                       'customer_object': customer_object,
                                                                       'errors': errors})
        if amount < 500:
            errors.append('已缴费用：最少为500！')
            return render(request, 'sales/registration_payment.html', {'enrollment_object': enrollment_object,
                                                                       'customer_object': customer_object,
                                                                       'errors': errors})
        else:
            models.Payment.objects.create(
                customer=customer_object,
                course=enrollment_object.enrolled_class.course,
                amount=amount,
                consultant=enrollment_object.consultant,
            )
            enrollment_object.contract_approved = True
            enrollment_object.save()
            customer_object.status = 0
            customer_object.save()
            return redirect('/kingadmin/crm/customer/')
