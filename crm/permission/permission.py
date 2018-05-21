# !/usr/bin/python3
# -*- coding:utf-8 -*-

from django.shortcuts import HttpResponse, redirect
from django.core.urlresolvers import resolve

from crm.permission import permission_list


def perm_check(*args, **kwargs):
    request = args[0]
    if request.user.is_authenticated():
        print('--request path--: ', request.path)
        for permission_name, v in permission_list.perm_dic.items():
            # print(permission_name, v)
            url_matched = False
            if v['url_type'] == 1:
                print(v['url'])
                if v['url'] == request.path:
                    print('xiang')
                    url_matched = True
            else:
                resolve_url = resolve(request.path)
                print('--resolve_url--: ', resolve_url)
                if resolve_url.url_name == v['url']:
                    url_matched = True
                    print('okok')

            if url_matched:
                if v['method'] == request.method:
                    arg_matched = True
                    for request_arg in v['args']:
                        request_method_func = getattr(request, v['method'])
                        if not request_method_func.get(request_arg):
                            arg_matched = False

                    if arg_matched:
                        if request.user.has_perm(permission_name):
                            print('有权限')
                            return True
    else:
        return redirect('/account/login/')


def check_permission(func):
    def inner(*args, **kwargs):
        if perm_check(*args, **kwargs):
            return func(*args, **kwargs)
        else:
            return HttpResponse('没有权限')
    return inner