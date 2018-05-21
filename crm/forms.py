# !/usr/bin/python3
# -*- coding:utf-8 -*-

from django import forms
from crm import models


class EnrollmentModelForm(forms.ModelForm):

    def __new__(cls, *args, **kwargs):
        for field_name, field_object in cls.base_fields.items():
            if type(field_object.widget).__name__ == 'CheckboxInput':
                pass
            else:
                field_object.widget.attrs['class'] = 'form-control'
        return super(EnrollmentModelForm, cls).__new__(cls)

    class Meta:
        model = models.Enrollment
        fields = ['enrolled_class', 'consultant']


class StudentRegistrationModelForm(forms.ModelForm):
    def __new__(cls, *args, **kwargs):
        for field_name, field_object in cls.base_fields.items():
            if type(field_object.widget).__name__ == 'CheckboxInput':
                pass
            else:
                field_object.widget.attrs['class'] = 'form-control'
            if field_name in cls.Meta.readonly_fields:
                field_object.widget.attrs['disabled'] = True
        return super(StudentRegistrationModelForm, cls).__new__(cls)

    def clean(self):
        if self.Meta.readonly_fields:
            for readonly_name in self.Meta.readonly_fields:
                field_db_value = getattr(self.instance, readonly_name, '')
                field_web_value = self.cleaned_data.get(readonly_name, '')
                if hasattr(field_web_value, 'select_related'):
                    field_db_value = [str(i[0]) for i in field_db_value.select_related.values_list('id')].sort()
                    field_web_value = [str(i[0]) for i in field_web_value.select_related.values_list('id')].sort()
                    if field_db_value != field_web_value:
                        self.add_error(readonly_name, '只读字段不可以修改！')
                        continue
                if field_web_value != field_db_value:
                    self.add_error(readonly_name, '只读字段不可以修改！')
        return self.cleaned_data

    class Meta:
        model = models.Customer
        fields = '__all__'
        exclude = ['tags', 'content', 'memo', 'status', 'consult_course', 'referral_from']
        readonly_fields = ['source', 'consultant']
