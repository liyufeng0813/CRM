# !/usr/bin/python3
# -*- coding:utf-8 -*-

from django import template
from django.db.models import Sum


register = template.Library()


@register.simple_tag
def get_score(enrollment, customer):
    study_records = enrollment.studyrecord_set.filter(course_record__from_class_id=enrollment.enrolled_class_id)
    score = study_records.aggregate(Sum('score'))['score__sum']
    return score
