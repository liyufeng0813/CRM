# !/usr/bin/python3
# -*- coding:utf-8 -*-

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


def account_login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        account = authenticate(username=email, password=password)
        if account:
            login(request, account)
            redirect_url = request.GET.get('next', '/crm/index/')
            return redirect(redirect_url)
        errors = '用户名或者密码不正确！'
        return render(request, 'account_login.html', {'errors': errors, 'email': email, 'password': password})
    return render(request, 'account_login.html')


def account_logout(request):
    logout(request)
    return redirect('/account/login/')


@login_required
def index(request):
    return render(request, 'index.html')
