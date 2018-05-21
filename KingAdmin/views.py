import re

from django.shortcuts import render, redirect, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import ugettext as _
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from KingAdmin import king_admin, utils, forms


@login_required
def index(request):
    return render(request, 'kingadmin/table_index.html', {'table_list': king_admin.enabled_admins})


@login_required
def display_table_objs(request, app_name, table_name):
    admin_class = king_admin.enabled_admins[app_name][table_name]

    if request.method == 'POST':
        action = request.POST.get('action', '')
        action_id = request.POST.get('action_id', '')
        if action and action_id:
            action_selected_object = admin_class.model.objects.filter(id__in=action_id.split(','))
        else:
            action_selected_object = []

        if action in admin_class.actions:
            action_func = getattr(admin_class, action)
            request.action = action
            request.action_id = action_id
            return action_func(admin_class, request, action_selected_object)

    object_list, filter_conditions = utils.table_filter(request, admin_class)   # 过滤条件过滤
    object_list, order_by_key = utils.table_sort(object_list, request, admin_class)    # 排序字段排序
    object_list, search_key = utils.table_search(request, object_list, admin_class)     # 搜索条件搜索
    paginator = Paginator(object_list, admin_class.list_page)

    page_num = request.GET.get('page', 1)
    try:
        query_sets = paginator.page(page_num)
    except PageNotAnInteger:
        query_sets = paginator.page(1)
    except EmptyPage:
        query_sets = paginator.page(paginator.num_pages)

    return render(request, 'kingadmin/table_objs.html', {'admin_class': admin_class,
                                                         'query_sets': query_sets,
                                                         'filter_conditions': filter_conditions,
                                                         'order_by_key': order_by_key,
                                                         'search_key': search_key})


@login_required
def table_object_change(request, app_name, table_name, object_id):
    admin_class = king_admin.enabled_admins[app_name][table_name]
    modelform = forms.create_modelform(admin_class)
    model_object = admin_class.model.objects.get(id=object_id)
    delete_url_args = {'app_name': app_name, 'table_name': table_name, 'object_id': object_id}

    if admin_class.readonly_table:
        return redirect(reverse('table_objs', kwargs={'app_name': app_name, 'table_name': table_name}))
    if request.method == 'GET':
        form_object = modelform(instance=model_object)
    elif request.method == 'POST':
        form_object = modelform(request.POST, instance=model_object)
        if form_object.is_valid():
            form_object.save()
            url = re.sub(r'/\w+/change', '', request.path)      # 数据通过验证，跳转到首页。
            return redirect(url)
    else:
        form_object = modelform(instance=model_object)
    return render(request, 'kingadmin/table_obj_change.html', {'form_object': form_object,
                                                               'admin_class': admin_class,
                                                               'delete_url_args': delete_url_args})


@login_required
def table_object_add(request, app_name, table_name):
    admin_class = king_admin.enabled_admins[app_name][table_name]
    admin_class._add_form = True
    modelform = forms.create_modelform(admin_class)

    if admin_class.readonly_table or admin_class.readonly_all_fields:
        # 如果这个表是只读的，不能进入add页面。
        return redirect('/kingadmin/{}/{}'.format(app_name, table_name))
    if request.method == 'GET':
        form_object = modelform()
    elif request.method == 'POST':
        form_object = modelform(request.POST)
        if form_object.is_valid():
            form_object.save()
            url = re.sub(r'/add', '', request.path)
            return redirect(url)
    else:
        form_object = modelform()
    return render(request, 'kingadmin/table_obj_add.html', {'form_object': form_object,
                                                            'admin_class': admin_class})


@login_required
def table_object_delete(request, app_name, table_name, object_id):
    admin_class = king_admin.enabled_admins[app_name][table_name]
    model_objects = admin_class.model.objects.filter(id=object_id)
    url = re.sub(r'/delete', '/change', request.path)

    if admin_class.readonly_table or admin_class.readonly_all_fields:
        return redirect(reverse('table_objs', kwargs={'app_name': app_name, 'table_name': table_name}))
    if request.method == 'POST':
        model_objects.delete()
        return redirect(re.sub(r'/\d+/delete', '', request.path))
    return render(request, 'kingadmin/table_obj_delete.html', {'model_objects': model_objects,
                                                               'url': url})


@login_required
def password_reset(request, app_name, table_name, object_id):
    admin_class = king_admin.enabled_admins[app_name][table_name]
    model_object = admin_class.model.objects.get(id=object_id)

    if request.method == 'GET':
        form_object = forms.PasswordResetForm()
    elif request.method == 'POST':
        form_object = forms.PasswordResetForm(request.POST)
        if form_object.is_valid():
            password = form_object.cleaned_data.get('password1')
            model_object.set_password(password)
            model_object.save()
            return redirect(reverse('table_object_change',
                                    kwargs={'app_name': app_name, 'table_name': table_name, 'object_id': object_id}))
    else:
        form_object = forms.PasswordResetForm()
    return render(request, 'kingadmin/password_reset.html', {'form_object': form_object,
                                                             'model_object': model_object})
