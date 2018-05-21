# !/usr/bin/python3
# -*- coding:utf-8 -*-

from django.db.models import Q


def table_filter(request, admin_class):
    """
    :param request: request对象
    :param admin_class: admin_class对象
    :return: 根据输入条件过滤的 对象列表和过滤条件的字典
    """
    filter_conditions = {}
    for k, v in request.GET.items():
        if k not in admin_class.list_filter:
            # 如果输入的条件不在设置的过滤条件内，跳过此次循环，避免输入数据库中不存在的字段，引发错误
            continue
        if v:
            # 如果用户输入的条件有值
            if k in admin_class.list_display_date:
                k += '__gte'
                # 如果是 按时间过滤，在date关键字上加上 __gte
            filter_conditions[k] = v
    try:
        object_list = admin_class.model.objects.filter(**filter_conditions).order_by('id').select_related()
        # 对查询进行异常处理，如果查询异常，返回全部数据。
    except Exception:
        object_list = admin_class.model.objects.all().order_by('id').select_related()

    return object_list, filter_conditions


def table_sort(object_list, request, admin_class):
    """
    返回按排序要求的数据集 和 排序字段。
    如果页面输入 o=id,需要按id的正序排列，那么首先把数据按id排列，然后把id的相反 -id 返回给页面，用来控制页面排序的a标签的href。
    页面点击id想要按id排序，后台返回按id排好的数据和-id给页面，页面再把-id加到原来id参数的位置，这样 页面再点击id标签时，标签的href是 -id，
    这样就把 -id 发到了后台，再按id的降序排列数据，形成循环。正序 - 倒序 - 正序 - ...
    """
    order_by_key = request.GET.get('o', '')
    if order_by_key.lstrip('-') in admin_class.list_display:    # 判断输入的要排序的字段是合法，也就是输入的字段在允许排序的字段中
        if order_by_key.startswith('-'):    # 如果输入的字段以 - 开头，也就是倒序时，把正序字段传到页面
            order_by_key = order_by_key.lstrip('-')     # 对order_by_key参数进行处理，把 ---id 这种数据变成 -id，
            order_by_key = '-' + order_by_key           # 避免 直接使用 ---id 这种不正常参数，直接filter查询，从而报错
            object_list = object_list.order_by(order_by_key)
            order_by_key = order_by_key.lstrip('-')
        else:
            object_list = object_list.order_by(order_by_key)
            order_by_key = '-' + order_by_key
    else:
        order_by_key = ''
    return object_list, order_by_key


def table_search(request, object_list, admin_class):
    search = request.GET.get('searchData', '')
    if search:
        q = Q()
        q.connector = 'OR'      # q 对象内部关系是 or
        for search_item in admin_class.search_fields:
            search_info = search_item + '__contains'    # name__contains 模糊搜索
            q.children.append((search_info, search))
        object_list = object_list.filter(q)
    return object_list, search
