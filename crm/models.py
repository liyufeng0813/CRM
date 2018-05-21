from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, ValidationError
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin
)
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe


def phone_check(phone):
    if not phone.isdigit():
        raise ValidationError('手机号码必须是数字', code='invalid')


class Customer(models.Model):
    """客户信息表 QQ做唯一标识"""
    name = models.CharField(verbose_name='客户名', max_length=64, blank=True, null=True)
    email = models.EmailField(verbose_name='邮箱', max_length=256)
    ID_number = models.CharField(verbose_name='身份证号码', max_length=128)
    qq = models.CharField(verbose_name='QQ', max_length=64, unique=True, validators=[RegexValidator(r'^\d+$', 'qq只能为数字', 'invalid')])
    qq_name = models.CharField(verbose_name='QQ名', max_length=64, blank=True, null=True)
    phone = models.CharField(verbose_name='电话', max_length=64, blank=True, null=True, validators=[phone_check])
    source_choices = (
        (0, '转介绍'),
        (1, 'QQ群'),
        (2, '官网'),
        (3, '百度推广'),
        (4, '51CTO'),
        (5, '知乎'),
        (6, '市场推广'),
        (7, '其他'),
    )
    source = models.SmallIntegerField(verbose_name='客户来源', choices=source_choices)
    referral_from = models.CharField(verbose_name='转介绍人QQ', max_length=64, blank=True, null=True)
    consult_course = models.ForeignKey(to='Course', verbose_name='咨询课程')
    content = models.TextField(verbose_name='咨询详情')
    consultant = models.ForeignKey(to='UserProfile', verbose_name='咨询顾问')
    date = models.DateTimeField(verbose_name='咨询日期', auto_now_add=True)
    memo = models.TextField(verbose_name='备注', blank=True, null=True)
    tags = models.ManyToManyField(to='Tag', verbose_name='标签')
    status_choices = (
        (0, '已报名'),
        (1, '未报名'),
    )
    status = models.SmallIntegerField(verbose_name='是否报名', choices=status_choices, default=1)

    def __str__(self):
        return self.qq

    class Meta:
        verbose_name = '客户信息表'
        verbose_name_plural = '客户信息表'


class Tag(models.Model):
    """标签表"""
    name = models.CharField(verbose_name='标签名', unique=True, max_length=64)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '标签表'


class CustomerFollowUp(models.Model):
    """客户跟进表"""
    customer = models.ForeignKey(to='Customer', verbose_name='客户名')
    content = models.TextField(verbose_name='跟进内容')
    consultant = models.ForeignKey(to='UserProfile', verbose_name='咨询顾问')
    date = models.DateTimeField(auto_now_add=True, verbose_name='咨询日期')
    intention_choices = (
        (0, '两周内报名'),
        (1, '一个月内报名'),
        (2, '近期无报名计划'),
        (3, '无意向'),
        (4, '已报名'),
        (5, '已拉黑'),
    )
    intention = models.SmallIntegerField(choices=intention_choices, verbose_name='客户意向')

    def __str__(self):
        return '{} : {}'.format(self.customer.qq, self.intention)

    class Meta:
        verbose_name_plural = '客户跟进表'


class Course(models.Model):
    """课程表"""
    name = models.CharField(verbose_name='课程名', max_length=64, unique=True)
    price = models.PositiveIntegerField(verbose_name='课程价格')
    period = models.PositiveIntegerField(verbose_name='课程周期(月)')
    outline = models.TextField(verbose_name='课程大纲')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '课程表'


class Branch(models.Model):
    """校区表"""
    name = models.CharField(max_length=128, unique=True, verbose_name='校区名')
    addr = models.CharField(max_length=256, verbose_name='校区地址')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '校区表'


class ClassList(models.Model):
    """班级表"""
    branch = models.ForeignKey(to='Branch', verbose_name='校区')
    course = models.ForeignKey(to='Course', verbose_name='课程')
    contract_templace = models.ForeignKey(to='ContractTemplate', blank=True, null=True)
    semester = models.PositiveSmallIntegerField(verbose_name='学期')
    teachers = models.ManyToManyField(to='UserProfile', verbose_name='老师')
    class_type_choices = (
        (0, '面授(脱产)'),
        (1, '面授(周末)'),
        (2, '网络班'),
    )
    class_type = models.SmallIntegerField(verbose_name='班级类型', choices=class_type_choices)
    start_date = models.DateField(verbose_name='开班日期')
    end_data = models.DateField(verbose_name='结业日期', blank=True, null=True)

    def __str__(self):
        return '{} : {} : {}'.format(self.branch, self.course, self.semester)

    class Meta:
        unique_together = ('branch', 'course', 'semester')
        verbose_name_plural = '班级表'


class CourseRecord(models.Model):
    """老师上课记录表"""
    from_class = models.ForeignKey(to='ClassList', verbose_name='班级名')
    day_num = models.PositiveSmallIntegerField(verbose_name='第几节(天)')
    teacher = models.ForeignKey(to='UserProfile', verbose_name='老师')
    has_homework = models.BooleanField(verbose_name='是否有作业', default=True)
    homework_title = models.CharField(verbose_name='作业题目', max_length=256, blank=True, null=True)
    homework_content = models.TextField(verbose_name='作业内容', blank=True, null=True)
    outline = models.TextField(verbose_name='本节课程大纲')
    date = models.DateField(verbose_name='上课日期', auto_now_add=True)

    def __str__(self):
        return '{} : {}'.format(self.from_class, self.day_num)

    class Meta:
        unique_together = ('from_class', 'day_num')
        verbose_name_plural = '老师上课记录表'


class StudyRecord(models.Model):
    """学员学习记录表"""
    student = models.ForeignKey(to='Enrollment', verbose_name='学员')
    course_record = models.ForeignKey(to='CourseRecord', verbose_name='课程')
    attendance_choices = (
        (0, '已签到'),
        (1, '迟到'),
        (2, '缺勤'),
        (3, '早退'),
    )
    attendance = models.SmallIntegerField(verbose_name='考勤', choices=attendance_choices)
    score_choices = (
        (100, 'A+'),
        (90, 'A'),
        (85, 'B+'),
        (80, 'B'),
        (75, 'B-'),
        (70, 'C+'),
        (60, 'C'),
        (40, 'C-'),
        (40, 'C-'),
        (-50, 'D'),
        (-100, 'COPY'),
        (0, 'N/A'),
    )
    score = models.SmallIntegerField(verbose_name='成绩', choices=score_choices)
    memo = models.TextField(verbose_name='备注', blank=True, null=True)
    date = models.DateField(verbose_name='日期', auto_now_add=True)

    def __str__(self):
        return '{} : {} : {}'.format(self.student, self.course_record, self.score)

    class Meta:
        verbose_name_plural = '学员上课记录表'
        unique_together = ('student', 'course_record')


class Enrollment(models.Model):
    """学员报名表"""
    customer = models.ForeignKey(to='Customer', verbose_name='学员')
    enrolled_class = models.ForeignKey(to='ClassList', verbose_name='所报班级')
    consultant = models.ForeignKey(to='UserProfile', verbose_name='课程顾问')
    contract_agreed = models.BooleanField(verbose_name='学员已同意合同', default=False)
    contract_approved = models.BooleanField(verbose_name='合同已审核', default=False)
    date = models.DateTimeField(verbose_name='报名时间', auto_now_add=True)

    def __str__(self):
        return '{} : {}'.format(self.customer, self.enrolled_class)

    class Meta:
        unique_together = ('customer', 'enrolled_class')
        verbose_name_plural = '学员报名表'


class Payment(models.Model):
    """缴费记录表"""
    customer = models.ForeignKey(to='Customer', verbose_name='客户')
    course = models.ForeignKey(to='Course', verbose_name='所报课程')
    amount = models.PositiveIntegerField(verbose_name='数额')
    consultant = models.ForeignKey(to='UserProfile', verbose_name='课程顾问')
    date = models.DateTimeField(verbose_name='缴费时间', auto_now_add=True)

    def __str__(self):
        return '{} : {}'.format(self.customer, self.course)

    class Meta:
        verbose_name_plural = '学员缴费记录表'


# class UserProfile(models.Model):
#     """账号表 讲师 销售 ..."""
#     user = models.OneToOneField(to=User)
#     name = models.CharField(verbose_name='账号名', max_length=64)
#     roles = models.ManyToManyField(verbose_name='角色', to='Role')
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         verbose_name_plural = '账号表'


class UserProfileManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            name=name,
        )

        user.set_password(password)
        user.save(using=self._db)
        user.active = True
        return user

    def create_superuser(self, email, name, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
            name=name,
        )
        user.is_admin = True
        user.save(using=self._db)
        user.active = True
        return user


class UserProfile(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name='邮箱',
        max_length=255,
        unique=True,
    )
    password = models.CharField(_('password'), max_length=128,
                                help_text=mark_safe('<a id="password_reset">点击修改密码</a>'))
    name = models.CharField(verbose_name='用户名', max_length=64)
    roles = models.ManyToManyField(verbose_name='用户类型', to='Role')
    is_active = models.BooleanField(default=True, verbose_name='是否活跃')
    is_admin = models.BooleanField(default=False, verbose_name='是否是管理员')
    student_account = models.ForeignKey(to='Customer', blank=True, null=True, verbose_name='学员', help_text='只有报名的客户，才可以关联学员账号。')

    objects = UserProfileManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __str__(self):              # __unicode__ on Python 2
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

    class Meta:
        verbose_name_plural = '账号表'


class Role(models.Model):
    """用户类型表"""
    name = models.CharField(verbose_name='角色类型', max_length=64, unique=True)
    menus = models.ManyToManyField(to='Menu', verbose_name='菜单')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '用户类型表'


class Menu(models.Model):
    """菜单表"""
    name = models.CharField(max_length=32, verbose_name='菜单名')
    url_name = models.CharField(max_length=64, unique=True, verbose_name='URL别名')
    url_type_choices = ((0, 'alias'), (1, 'absolute'))
    url_type = models.SmallIntegerField(verbose_name='url类型', choices=url_type_choices)
    absolute_url = models.CharField(max_length=126, verbose_name='url绝对路径', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '菜单表'


class ContractTemplate(models.Model):
    """合同模板"""
    name = models.CharField(verbose_name='合同名称', max_length=128)
    template = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '合同模板表'
