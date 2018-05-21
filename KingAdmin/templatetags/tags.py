# !/usr/bin/python3
# -*- coding:utf-8 -*- 

from django import template
from django.utils.safestring import mark_safe
from django.utils.timezone import datetime, timedelta
from django.core.exceptions import FieldDoesNotExist


register = template.Library()

@register.simple_tag
def render_model_name(admin_class):
    return admin_class.model._meta.verbose_name_plural


@register.simple_tag
def get_query_sets(admin_class):
    return admin_class.model.objects.all().select_related()


@register.simple_tag
def build_row_element(obj, admin_class, request):
    row_element = ""
    for index, column in enumerate(admin_class.list_display):
        try:
            field_obj = obj._meta.get_field(column)     # 拿到对应的字段对象
            if field_obj.choices:   # 该字段对象的choices属性是否有值
                column_data = getattr(obj, 'get_{}_display'.format(column))()   # 拿到model对象的此字段的choices值（显示的值），不是存到数据库中的值。
            elif type(field_obj).__name__ == 'DateTimeField':
                field = getattr(obj, column)
                column_data = field.strftime("%Y-%m-%d %H:%M:%S")
            else:
                column_data = getattr(obj, column)

            if index == 0:      # 第一位改为a标签，用来跳转修改页面
                row_element += '<td><a href="{}{}/change">{}</a></td>'.format(request.path, obj.id, column_data)
            else:
                row_element += "<td>{}</td>".format(column_data)
        except FieldDoesNotExist:
            custom_func = getattr(admin_class, column, '')
            row_element += '<td><a href="/crm/customer/{}/enrollment/">{}</a></td>'.format(obj.id, custom_func())
    return mark_safe(row_element)


@register.simple_tag
def render_page_element(page, query_sets, filter_conditions):
    filter_href = ''
    for k, v in filter_conditions.items():
        filter_href += '&{}={}'.format(k, v)
    if abs(page - query_sets.number) <= 3:
        element_class = ''
        if page == query_sets.number:
            element_class = 'active'
        page_element = '<li class={}><a href="?page={}{}">{}</a></li>'.format(element_class, page, filter_href, page)
        return mark_safe(page_element)
    return ''


@register.simple_tag
def build_page_button(query_sets, filter_conditions, order_by_key, search_key):
    """
    返回页码按钮类似 1 2 ... 4 5 6 7 8 ... 10 11。
    前后有两个固定页码标签， 当前页码标签前后各固定俩个页码标签， 多余的标签用 ... 代替。
    """
    filter_href = ''
    if 'page' in filter_conditions.keys():
        filter_conditions.__delitem__('page')
    if 'o' in filter_conditions.keys():
        filter_conditions.__delitem__('o')
    for k, v in filter_conditions.items():
        filter_href += '&{}={}'.format(k, v)
    order_by_key = order_by_key.lstrip('-') if order_by_key.startswith('-') else '-' + order_by_key
    # 后台返回的 order_by_key 与当前的url上的 是相反的，所以在后台返回的数据上，再取反，以达到和url上的o参数是一样的
    filter_href += '&{}={}'.format('o', order_by_key)
    filter_href += '&{}={}'.format('searchData', search_key)
    page_button_element = ''
    add_dot = False     # 是否加了 ... 标签的标志位
    for page_num in query_sets.paginator.page_range:
        if page_num <= 2 or page_num >= query_sets.paginator.num_pages - 1 \
                or abs(query_sets.number - page_num) <= 2:
            # 前后有两个固定页码标签， 当前页码标签前后各固定俩个页码标签， 多余的标签用 ... 代替
            element_class = ''
            if page_num == query_sets.number:
                add_dot = False
                # 可能当前页码标签的前后个需要一个 ... 标签，当遍历到当前标签时，重置标志位，让后面也生成一个 ... 标签
                element_class = 'active'
            page_button_element += '<li class={}><a href="?page={}{}">{}</a></li>'.format(element_class, page_num, filter_href, page_num)
        else:
            if not add_dot:
                page_button_element += '<li><a href="javascript: void(0)">...</a></li>'
                add_dot = True
    return mark_safe(page_button_element)


@register.simple_tag
def render_filter_element(filter_field, admin_class, filter_conditions):
    """
    用户输入搜索结果，在搜索框内显示搜索的条件。
    """
    select_element = '<select class="form-control" name="{}" id=""><option value="">------</option>'.format(filter_field)
    field_obj = admin_class.model._meta.get_field(filter_field)
    if field_obj.choices:
        # 如果字段的choices有值，那么这个字段是select或者checkbox标签
        for choice_item in field_obj.choices:
            selected = ''
            if filter_conditions.get(filter_field, None) and str(choice_item[0]) == filter_conditions[filter_field]:
                # 如果传进来的条件有值，且条件值等于循环的值，就把标签加上selected属性，表示已被选择
                selected = 'selected'
                select_element += '<option value="{}" {}>{}</option>'.format(choice_item[0], selected, choice_item[1])
            else:
                select_element += '<option value="{}" {}>{}</option>'.format(choice_item[0], selected, choice_item[1])

    if type(field_obj).__name__ == 'ForeignKey':
        # 判断字段是否是外键
        for foreign_choice_item in field_obj.get_choices()[1:]:
            selected = ''
            if filter_conditions.get(filter_field, None) and str(foreign_choice_item[0]) == filter_conditions[filter_field]:
                selected = 'selected'
                select_element += '<option value="{}" {}>{}</option>'.format(foreign_choice_item[0], selected, foreign_choice_item[1])
            else:
                select_element += '<option value="{}" {}>{}</option>'.format(foreign_choice_item[0], selected, foreign_choice_item[1])

    if type(field_obj).__name__ in ['DateTimeField', 'DateField']:
        select_element = '<select class="form-control" name="{}" id=""><option value="">------</option>'.format(filter_field)
        current_date = datetime.now().date()
        date = {}
        date['今天'] = current_date
        date['昨天'] = current_date - timedelta(days=1)
        date['近7天'] = current_date - timedelta(days=7)
        date['近30天'] = current_date - timedelta(days=30)
        date['近90天'] = current_date - timedelta(days=90)
        date['近180天'] = current_date - timedelta(days=180)
        date['近365天'] = current_date - timedelta(days=365)
        date['本月'] = current_date.replace(day=1)
        date['本年'] = current_date.replace(month=1, day=1)

        filter_field += '__gte'
        for k, v in date.items():
            if filter_conditions.get(filter_field, None) and filter_conditions[filter_field] == v.__str__():
                selected = 'selected'
            else:
                selected = ''
            select_element += '<option value="{}" {}>{}</option>'.format(v, selected, k)

    select_element += '</select>'
    return mark_safe(select_element)


@register.simple_tag
def get_filter_conditions_href(page, filter_conditions, order_by_key, search_key):
    """
    把搜索条件和page参数拼接在一起，避免 搜索结果有两页时，点击下一页等a标签，不会保存搜索结果。
    生成这种连接 '?page=2&source=2&consultant=1'
    """
    order_by_key = order_by_key.lstrip('-') if order_by_key.startswith('-') else '-' + order_by_key
    # 后台返回的 order_by_key 与当前的url上的 是相反的，所以在后台返回的数据上，再取反，以达到和url上的o参数是一样的
    filter_href = '?page={}'.format(page)
    filter_href += '&{}={}'.format('o', order_by_key)
    filter_href += '&{}={}'.format('searchData', search_key)
    for k, v in filter_conditions.items():
        filter_href += '&{}={}'.format(k, v)
    return filter_href


@register.simple_tag
def build_header_column(column, order_by_key, filter_conditions, search_key, admin_class):
    """生成排序的标签"""
    filter_href = ''
    if 'o' in filter_conditions.keys():
        del filter_conditions['o']
    for k, v in filter_conditions.items():
        filter_href += '&{}={}'.format(k, v)
    filter_href += '&{}={}'.format('searchData', search_key)
    element = '<a href="?o={order_by_key}{filter_href}">{column} {order_icon}</span></a>'
    if order_by_key.lstrip('-') == column:  # 如果是按这个字段排序
        if order_by_key.startswith('-'):
            order_icon = '<span class="glyphicon glyphicon-chevron-down" aria-hidden="true">'
        else:
            order_icon = '<span class="glyphicon glyphicon-chevron-up" aria-hidden="true">'
    else:
        order_by_key = '-' + column
        order_icon = ''

    try:
        """
        获取字段的verbose_name，有则显示，没有则显示字段名。
        进行异常处理，可以判断出这个字段是数据库中的字段还是用户在kingdmin内自定义的，如果是自定义的用span标签。
        """
        column_verbose_name = admin_class.model._meta.get_field(column).verbose_name
        column = column_verbose_name
        ele = element.format(order_by_key=order_by_key, filter_href=filter_href, order_icon=order_icon, column=column)
    except FieldDoesNotExist:
        if hasattr(getattr(admin_class, column), 'display_name'):
            # 如果自定义的字段有 dispaly_name属性，就显示diaplay_name。
            column = getattr(admin_class, column).display_name
        ele = '<a href="javascript:void(0);">{}</a>'.format(column)
    return mark_safe(ele)


@register.simple_tag
def get_table_name(obj):
    if hasattr(obj, 'model'):
        table_name = obj.model._meta.verbose_name_plural
    else:
        table_name = obj._meta.verbose_name_plural
    return table_name


@register.simple_tag
def get_m2m_objects_select(admin_class, field, form_object):
    """返回m2m字段 所有待选数据"""
    # 表的多对多字段的数据，即全部对象
    field_object = getattr(admin_class.model, field.name)
    m2m_select_list = field_object.rel.to.objects.all().select_related()

    if form_object.instance.id:
        # 数据库实例的多对多字段的数据，即已选择的
        selected_list = getattr(form_object.instance, field.name).all()
    else:
        # 如果instance没有值，那么是创建数据的时候，直接返回全部数据就行。
        return m2m_select_list

    # 拿到待选的字段，即全部对象 - 已选择的
    wait_select_list = []
    for obj in m2m_select_list:
        if obj not in selected_list:
            wait_select_list.append(obj)
    return wait_select_list


@register.simple_tag
def get_m2m_objects_selected(form_object, field):
    """返回所有已经选择的数据"""
    if form_object.instance.id:
        # 如果instance有值，则说明是修改数据，
        obj = getattr(form_object.instance, field.name)
        m2m_selected_list = obj.all().select_related()
        return m2m_selected_list


@register.simple_tag
def build_related_element(model_objects):
    # model_object = [model_object, ]
    element = get_all_related_element(model_objects)
    return mark_safe(element)


def get_all_related_element(model_objects):
    base_ul_ele = '<ul>'
    for model_object in model_objects:
        href = '/{}/{}/{}/{}/change/'.format('kingadmin', model_object._meta.app_label, model_object._meta.model_name, model_object.id)
        base_li_ele = '<li>{} : <a href="{}">{}</a></li>'.format(model_object._meta.verbose_name, href, model_object.__str__())

        ul_ele = '<ul>'
        if model_object._meta.local_many_to_many:
            """自己这个表的多对多字段"""
            for m2m in model_object._meta.local_many_to_many:
                m2m_objects = getattr(model_object, m2m.name).select_related()
                for m2m_obj in m2m_objects:
                    li_ele = '<li>{}-{} 关系({})</li>'.format(model_object._meta.verbose_name, m2m_obj._meta.model_name, m2m_obj.__str__())
                    ul_ele += li_ele

        if model_object._meta.related_objects:
            """关联到自己这个表的其他表"""
            for rel_obj in model_object._meta.related_objects:
                if 'ManyToMany' in rel_obj.__repr__():
                    related_objects = getattr(model_object, rel_obj.get_accessor_name()).select_related()
                    for related_object in related_objects:
                        li_ele = '<li>{}-{} 关系({})</li>'.format(model_object._meta.verbose_name, related_object._meta.model_name, related_object.__str__())
                        ul_ele += li_ele
                elif 'OneToOne' in rel_obj.__repr__():
                    related_object = getattr(model_object, rel_obj.get_accessor_name())
                    href = '/kingadmin/{}/{}/{}/change/'.format(related_object._meta.app_label, related_object._meta.model_name, related_object.id)
                    li_ele = '<li>{} : <a href="{}">{}</a></li>'.format(related_object._meta.verbose_name, href, related_object.__str__())
                    ul_ele += li_ele
                    related_objects = [related_object]
                else:
                    related_objects = getattr(model_object, rel_obj.get_accessor_name()).select_related()
                    for related_object in related_objects:
                        href = '/kingadmin/{}/{}/{}/change'.format(related_object._meta.app_label, related_object._meta.model_name, related_object.id)
                        li_ele = '<li>{} : <a href="{}">{}</a></li>'.format(related_object._meta.verbose_name, href, related_object.__str__())
                        ul_ele += li_ele
                # if len(related_objects) > 0:
                    # """递归查询关联的数据"""
                    # li_ele = get_all_related_element(related_objects)
                    # ul_ele += li_ele
        ul_ele += '</ul>'
        base_li_ele += ul_ele

        base_ul_ele += base_li_ele
    base_ul_ele += '</ul>'
    return base_ul_ele


@register.simple_tag
def get_action_obj_verbose_name(action_obj, admin_class):
    action = getattr(admin_class, action_obj)
    if getattr(action, 'verbose_name', None):
        return action.verbose_name
    else:
        return action_obj


