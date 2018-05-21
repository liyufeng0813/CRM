import os
import json
import time

from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required

from crm import models
from PerfectCRM.settings import HOMEWORKS_PATH
from student import utils
from crm.permission.permission import check_permission


@login_required
def index(request):
    enrollment_list = request.user.student_account.enrollment_set.filter(contract_agreed=True,
                                                                         contract_approved=True).select_related()
    return render(request, 'student/index.html', {'enrollment_list': enrollment_list})


@login_required
def studyrecords(request, enrollment_id):
    enrollment_object = models.Enrollment.objects.get(id=enrollment_id)
    return render(request, 'student/studyrecords.html', {'enrollment_object': enrollment_object})


@login_required
@check_permission
def homework_detail(request, studyrecord_id):
    """
    获取前端传过来的文件，然后保存文件。
    保存文件的目录结构
        homeworks/课程名(c++...)/班级名(深圳校区 c++ 2...)/第几节课(第1节课...)/作业的文件名(mike的作业.zip...)
    """
    studyrecord_object = models.StudyRecord.objects.get(id=studyrecord_id)
    catalog_path = '{}/{}/{}'.format(HOMEWORKS_PATH,
                                     studyrecord_object.course_record.from_class.course.name,
                                     studyrecord_object.course_record.from_class.__str__().replace(':', ''))
    catalog_path = '{}/{}{}{}'.format(catalog_path, '第', studyrecord_object.course_record.day_num, '节课')
    if request.method == 'POST':
        if not os.path.exists(catalog_path):
            os.makedirs(catalog_path, exist_ok=True)

        file_list = []
        for k, file in request.FILES.items():
            file_path = '{}/{}-{}'.format(catalog_path, studyrecord_object.student.id, file.name)
            with open(file_path, 'wb') as f:
                for chunk in file.chunks():
                    f.write(chunk)

            file_dict = {'file_name': '{}-{}'.format(studyrecord_object.student.id, file.name),
                         'file_size': utils.get_size(file.size),
                         'file_time': utils.get_time(time.time())}
            file_list.append(file_dict)
            # 由于是ajax提交的，返回 file_list 给前端用来生成对应的tr的标签
        return HttpResponse(json.dumps({'status': 0, 'message': 'file upload success', 'file_list': file_list}))

    file_list = utils.get_file_list(catalog_path)
    return render(request, 'student/homework_detail.html', {'studyrecord_object': studyrecord_object,
                                                            'file_list': file_list})


@login_required
def homework_delete(request, studyrecord_id):
    """删除上传的文件"""
    if request.method == 'POST':
        filename = request.POST.get('filename', '')
        studyrecord_object = models.StudyRecord.objects.get(id=studyrecord_id)
        catalog_path = '{}/{}/{}'.format(HOMEWORKS_PATH,
                                         studyrecord_object.course_record.from_class.course.name,
                                         studyrecord_object.course_record.from_class.__str__().replace(':', ''))
        catalog_path = '{}/{}{}{}'.format(catalog_path, '第', studyrecord_object.course_record.day_num, '节课')
        file_path = '{}/{}'.format(catalog_path, filename)
        try:
            os.remove(file_path)
        except FileNotFoundError:
            return HttpResponse(json.dumps({'status': 1, 'message': '文件删除失败'}))
        return HttpResponse(json.dumps({'status': 0, 'message': '文件删除成功', 'filename': filename}))
