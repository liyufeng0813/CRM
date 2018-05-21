# !/usr/bin/python3
# -*- coding:utf-8 -*-

from django import forms
from django.utils.translation import gettext as _
from django.forms import ValidationError

from crm import models


class CustomerModelForm(forms.ModelForm):
    class Meta:
        model = models.Customer
        fields = '__all__'


def create_modelform(admin_class):
    """动态生成 ModelForm对象

    class DynamicModelForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            for field_name, field_object in self.base_fields.items():
                field_object.widget.attrs['class'] = 'form-control'

            super(forms.ModelForm, self).__init__(*args, **kwargs)

        class Meta:
            model = admin_class.model
            fields = '__all__'
    """

    def __init__(self, *args, **kwargs):

        for field_name, field_object in self.base_fields.items():
            if not getattr(admin_class, '_add_form', ''):
                if field_name in admin_class.readonly_fields:
                    field_object.widget.attrs['disabled'] = True

            if type(field_object.widget).__name__ == 'CheckboxInput':
                pass
            else:
                field_object.widget.attrs['class'] = 'form-control'

        super(forms.ModelForm, self).__init__(*args, **kwargs)

    def clean(self):
        """重写forms的clean方法，给所有的form字段加一个验证,
           先调用在admin_class中的default_clean方法，进行自定义的验证，把验证结果加到error_list中，
           再进行readonly字段的验证，最后把所有的error抛出。
        """
        if admin_class.readonly_all_fields:
            raise ValidationError('不能进行修改表的操作！', code='invalid')

        error_list = []
        try:
            # 对执行的函数进行异常处理，接收执行函数抛出的异常。
            admin_class.default_clean(self)     # 把modelform传到在king_admin文件内写的验证函数中，因为modelform中有cleaned_data。
        except ValidationError as e:
            error_list.append(e)

        if not getattr(admin_class, '_add_form', ''):
            # 如果是添加信息，就不需要进行readonly验证。
            cleaned_data = self.cleaned_data
            if admin_class.readonly_fields:
                # 判断只读字段提交的数据和数据库中的数据是否相同，不相同就抛出异常，因为是只读字段。
                for readonly_field_name in admin_class.readonly_fields:
                    field_db_value = getattr(self.instance, readonly_field_name, '')
                    field_web_value = cleaned_data.get(readonly_field_name, '')
                    # 多对多字段，前端传过来的是列表[1,2]，但是经过cleanen_data之后 会变成对应的对象。

                    if hasattr(field_web_value, 'select_related'):
                        # 如果传过来的对象有 'select_related'属性，也就是多对多字段。拿到对象的id，再对id这个列表排序，再和数据库中的数据比较。
                        field_db_value = [str(i[0]) for i in field_db_value.select_related().values_list('id')]
                        field_web_value = [str(i[0]) for i in field_web_value.select_related().values_list('id')]
                        field_web_value.sort()
                        field_db_value.sort()

                        if field_db_value != field_web_value:
                            error = ValidationError(
                                _('Field "%(field)s" is readonly"'),
                                code='invalid',
                                params={'field': readonly_field_name}
                            )
                            error_list.append(error)
                        continue

                    if field_db_value != field_web_value:
                        error = ValidationError(
                            _('Field "%(field)s" is readonly, data should be "%(value)s"'),
                            code='invalid',
                            params={'field': readonly_field_name, 'value': field_db_value}
                        )
                        error_list.append(error)

        if error_list:
            raise ValidationError(error_list)

    class Meta:
        model = admin_class.model
        fields = '__all__'
        exclude = admin_class.exclude_field

    attr = {
        'Meta': Meta,
        '__init__': __init__,
        'clean': clean,
    }
    _modelform = type('DynamicModelForm', (forms.ModelForm,), attr)     # 动态生成ModelForm类。
    return _modelform


class PasswordResetForm(forms.Form):
    password1 = forms.CharField(label='密码', max_length=126,
                                widget=forms.PasswordInput(attrs={'class': "form-control"}))
    password2 = forms.CharField(label='重复密码', max_length=126,
                                widget=forms.PasswordInput(attrs={'class': "form-control"}))

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8:
            self.add_error('password1', ValidationError('密码长度不能小于8！', code='invalid'))
        elif password1.isdigit():
            self.add_error('password1', ValidationError('密码长度不能全为数字！', code='invalid'))
        else:
            return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 != password2:
            self.add_error('password2', ValidationError('两次密码不相同', code='invalid'))
