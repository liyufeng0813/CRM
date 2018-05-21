from django.contrib import admin
from django.shortcuts import render, redirect, HttpResponse
from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.db import IntegrityError

from crm import models


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'qq', 'phone', 'source', 'consult_course', 'consultant', 'status', 'content', 'date')
    list_filter = ('source', 'status', 'consultant', 'consult_course', 'date')
    search_fields = ('qq', 'name', 'phone')
    # raw_id_fields = ('consult_course',)
    filter_horizontal = ('tags',)
    list_editable = ('status',)
    # list_per_page = 1
    # ordering = ('-qq',)
    # readonly_fields = ('name', 'qq', 'tags')

    actions = ['action_test']

    def action_test(self, request, arg):
        render(request, 'kingadmin/table_index.html')


class CourseRecordAdmin(admin.ModelAdmin):
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
                study_record_object = models.StudyRecord(
                    student=enrollment,
                    course_record=queryset[0],
                    attendance=0,
                    score=0,
                )
                study_record_list.append(study_record_object)
            try:
                models.StudyRecord.objects.bulk_create(study_record_list)
            except IntegrityError:
                return HttpResponse('批量生成学习记录时，出错了。可能原因：需要生成的学习记录，已经存在。 解决措施：删除已经存在的学习记录，或者手动创建。')
            return redirect('/admin/crm/studyrecord/?course_record__id__exact={}'.format(queryset[0].id))
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
                    study_record_object = models.StudyRecord(
                        student=enrollment,
                        course_record=query_set,
                        attendance=0,
                        score=0,
                    )
                    study_record_list.append(study_record_object)
                try:
                    models.StudyRecord.objects.bulk_create(study_record_list)
                except IntegrityError:
                    return HttpResponse('批量生成学习记录时，出错了。 可能原因：需要生成的学习记录，已经存在。 解决措施：删除已经存在的学习记录，或者手动创建。')
            return redirect('/admin/crm/studyrecord/')

    initialize_studyrecords.short_description = '初始化本节课所有学员的学习记录'


class StudyRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'course_record', 'attendance', 'score', 'date']
    list_filter = ['course_record', 'attendance', 'score']
    list_editable = ['attendance', 'score']


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = models.UserProfile
        fields = ('email', 'name')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = models.UserProfile
        fields = ('email', 'password', 'name', 'is_active', 'is_admin')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'name', 'is_admin')
    list_filter = ('is_admin',)
    fieldsets = (
        (None, {'fields': ('email', 'password', 'roles')}),
        ('Personal info', {'fields': ('name', 'student_account')}),
        ('Permissions', {'fields': ('is_admin', 'is_active', 'user_permissions', 'groups')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2')}
        ),
    )
    search_fields = ('email', 'name')
    ordering = ('email',)
    filter_horizontal = ('user_permissions', 'groups')

# Now register the new UserAdmin...
# admin.site.register(MyUser, UserAdmin)
# ... and, since we're not using Django's built-in permissions,
# unregister the Group model from admin.
admin.site.unregister(Group)


admin.site.register(models.Customer, CustomerAdmin)
admin.site.register(models.CustomerFollowUp)
admin.site.register(models.Enrollment)
admin.site.register(models.Course)
admin.site.register(models.ClassList)
admin.site.register(models.CourseRecord, CourseRecordAdmin)
admin.site.register(models.Branch)
admin.site.register(models.Role)
admin.site.register(models.Payment)
admin.site.register(models.StudyRecord, StudyRecordAdmin)
admin.site.register(models.Tag)
admin.site.register(models.UserProfile, UserAdmin)
admin.site.register(models.Menu)
admin.site.register(models.ContractTemplate)
