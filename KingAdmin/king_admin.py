# !/usr/bin/python3
# -*- coding:utf-8 -*-

from django.contrib.auth.models import User
from django.shortcuts import render, redirect, HttpResponse
from django.db import IntegrityError

from crm import models as crm_models


class BaseAdmin(object):
    list_display = []                           # 展示的字段
    list_filter = []                            # 可以按这些字段对数据进行过滤
    list_page = 20                              # 每页显示20条数据
    search_fields = []                          # 在对数据搜索时，只会匹配这些字段
    filter_horizontal = []                      # 只能是 m2m 字段
    actions = ['delete_selected_objects']       # 可以执行的方法
    readonly_fields = []                        # 设置只读的字段
    readonly_all_fields = False                 # 设置全部字段只读
    readonly_table = False                      # 设置这个表只读，不能查看表内每条数据的具体信息
    exclude_field = []                          # 不显示的字段

    def delete_selected_objects(self, request, querysets):
        url = '/kingadmin/{}/{}/'.format(self.model._meta.app_label, self.model._meta.model_name)
        if self.readonly_table or self.readonly_all_fields:
            return redirect(url)
        if request.POST.get('delete_querysets', '') == 'yes':
            querysets.delete()
            return redirect(url)
        return render(request, 'kingadmin/table_obj_delete.html', {'model_objects': querysets,
                                                                   'url': url})
    def default_clean(self):
        pass


class CustomerAdmin(BaseAdmin):
    list_display = ['id', 'qq', 'name', 'source', 'consultant', 'consult_course', 'date', 'status', 'enroll']
    list_filter = ['source', 'consultant', 'consult_course', 'date']
    list_page = 5
    search_fields = ['id', 'qq', 'name', 'consultant__name']    # consultant 外键字段加 __name,用于跨表查询
    filter_horizontal = ['tags']
    readonly_fields = ('name', 'qq', 'consultant', 'tags')    # 只读字段
    # readonly_all_fields = True
    actions = ['test_action']
    # readonly_table = True

    def test_action(self, request, queryset):
        return render(request, 'kingadmin/table_index.html')

    test_action.verbose_name = '测试函数'   # 给action 执行函数，起个别名。

    def default_clean(self):
        from django.forms import ValidationError
        content = self.cleaned_data.get('content', '')
        if len(content) < 10:
            raise ValidationError('Field "%(field)s" length is greater than "%(len)s"',
                                  code='invalid',
                                  params={'field': 'content', 'len': '10'})

    def enroll(self):
        return '报名'

    enroll.display_name = '报名链接'


class CourseRecordAdmin(BaseAdmin):
    list_display = ['id', 'from_class', 'day_num', 'teacher', 'has_homework', 'date']
    actions = ['initialize_studyrecords']

    def initialize_studyrecords(self, request, queryset):
        """
        根据班级的上课记录批量生成对应班级学生的学习记录
            len(queryset) == 1  批量生成一个班级的学习记录
            len(queryset) > 1 循环批量生成班级的学习记录

            创建学习记录表：
                1 循环 save() 保存，创建对象：
                    可以使用 get_or_create() 方法，不需要进行异常处理(可能多次创建一个对象，会触发unique异常)；
                    创建一个对象保存一个对象；
                    缺点：
                        对象每一次 save() 都会对数据库进行 commit 提交，如果对象数量多了之后，会影响性能。
                2 使用 bulk_create() 批量创建对象：
                    可以一次创建多个对象，对数据库的操作减少了，优化了性能；
                    方法内部启动了数据库的事务，即：所有的对象要么全部创建，要么全部不会创建。
            两种创建对象的方法各有优劣，视情况使用。。
        """
        if len(queryset) == 1:
            enrollment_queryset = queryset[0].from_class.enrollment_set.filter(contract_approved=True,
                                                                               contract_agreed=True).select_related()
            study_record_list = []
            for enrollment in enrollment_queryset:
                # models.StudyRecord.objects.get_or_create(
                #     student=enrollment,
                #     course_record=queryset[0],
                #     attendance=0,
                #     score=0,
                # )
                study_record_object = crm_models.StudyRecord(
                    student=enrollment,
                    course_record=queryset[0],
                    attendance=0,
                    score=0,
                )
                study_record_list.append(study_record_object)
            try:
                crm_models.StudyRecord.objects.bulk_create(study_record_list)
            except IntegrityError:
                return HttpResponse('批量生成学习记录时，出错了。可能原因：需要生成的学习记录，已经存在。 解决措施：删除已经存在的学习记录，或者手动创建。')
            return redirect('/kingadmin/crm/studyrecord/?course_record={}'.format(queryset[0].id))
        else:
            for query_set in queryset:
                enrollment_queryset = query_set.from_class.enrollment_set.filter(contract_approved=True,
                                                                                   contract_agreed=True).select_related()
                study_record_list = []
                for enrollment in enrollment_queryset:
                    # models.StudyRecord.objects.get_or_create(
                    #     student=enrollment,
                    #     course_record=query_set,
                    #     attendance=0,
                    #     score=0,
                    # )
                    study_record_object = crm_models.StudyRecord(
                        student=enrollment,
                        course_record=query_set,
                        attendance=0,
                        score=0,
                    )
                    study_record_list.append(study_record_object)
                try:
                    crm_models.StudyRecord.objects.bulk_create(study_record_list)
                except IntegrityError:
                    return HttpResponse('批量生成学习记录时，出错了。 可能原因：需要生成的学习记录，已经存在。 解决措施：删除已经存在的学习记录，或者手动创建。')
            return redirect('/kingadmin/crm/studyrecord/')

    initialize_studyrecords.verbose_name = '初始化本节课所有学员的学习记录'


class StudyRecordAdmin(BaseAdmin):
    list_display = ['id', 'student', 'course_record', 'attendance', 'score', 'date']
    list_filter = ['course_record', 'attendance', 'score']
    list_editable = ['attendance', 'score']


class CustomerFollowUpAdmin(BaseAdmin):
    list_display = ['customer', 'consultant', 'date']


class TagAdmin(BaseAdmin):
    list_display = ['name']


class UserProfileAdmin(BaseAdmin):
    list_display = ['name', 'email']
    readonly_fields = ['password']
    filter_horizontal = ['user_permissions', 'groups']
    exclude_field = ['last_login', 'is_superuser']


class CourseAdmin(BaseAdmin):
    list_display = ['name', 'price', 'period', 'outline']


class BranchAdmin(BaseAdmin):
    list_display = ['name', 'addr']


class ClassListAdmin(BaseAdmin):
    list_display = ['branch', 'course', 'semester', 'teachers', 'class_type', 'start_date', 'end_data']


# class CourseRecordAdmin(BaseAdmin):
#     list_display = ['from_class', 'day_num', 'teacher', 'has_homework', 'homework_title', 'homework_content', 'outline', 'date']


# class StudyRecordAdmin(BaseAdmin):
#     list_display = ['student', 'course_record', 'attendance', 'memo', 'score', 'date']


class EnrollmentAdmin(BaseAdmin):
    list_display = ['customer', 'enrolled_class', 'consultant', 'contract_agreed', 'contract_approved', 'date']


class PaymentAdmin(BaseAdmin):
    list_display = ['customer', 'course', 'amount', 'consultant', 'date']


class RoleAdmin(BaseAdmin):
    list_display = ['name', 'menus']


class MenuAdmin(BaseAdmin):
    list_display = ['name', 'url_name']


class UserAdmin(BaseAdmin):
    list_display = ['username']


enabled_admins = {}


def register(models_class, admin_class=None):
    """
    enabled_admins = {
        'app_name': {
            'model_name': admin_class
        }
    }
    """
    from django.db.models.fields.related import ManyToManyField

    for index, field_name in enumerate(admin_class.filter_horizontal):
        # 只能是 m2m 字段
        try:
            if not isinstance(models_class._meta.get_field(field_name), ManyToManyField):
                del admin_class.filter_horizontal[index]
        except Exception:
            admin_class.filter_horizontal.__delitem__(index)

    if models_class._meta.app_label not in enabled_admins:
        enabled_admins[models_class._meta.app_label] = {}

    admin_class.list_display_date = []
    try:
        list_display = admin_class.list_display
    except Exception:
        list_display = []
    if list_display:
        for index, item in enumerate(list_display):
            try:
                field_obj = models_class._meta.get_field(item)
            except Exception:
                field_obj = ''
            if type(field_obj).__name__ in ['DateField', 'DateTimeField']:
                admin_class.list_display_date.append(item)

    admin_class.actions += ['delete_selected_objects']
    admin_class.actions = list(set(admin_class.actions))

    admin_class.model = models_class    # 把model对象关联到admin_class上。
    enabled_admins[models_class._meta.app_label][models_class._meta.model_name] = admin_class


register(crm_models.Customer, CustomerAdmin)
register(crm_models.CustomerFollowUp, CustomerFollowUpAdmin)
register(crm_models.Tag, TagAdmin)
register(crm_models.UserProfile, UserProfileAdmin)
register(crm_models.Course, CourseAdmin)
register(crm_models.Branch, BranchAdmin)
register(crm_models.ClassList, ClassListAdmin)
register(crm_models.CourseRecord, CourseRecordAdmin)
register(crm_models.StudyRecord, StudyRecordAdmin)
register(crm_models.Enrollment, EnrollmentAdmin)
register(crm_models.Payment, PaymentAdmin)
register(crm_models.Role, RoleAdmin)
register(crm_models.Menu, MenuAdmin)
register(User, UserAdmin)