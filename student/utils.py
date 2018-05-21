# !/usr/bin/python3
# -*- coding:utf-8 -*-

import os
import time


def get_file_list(catalog_path):
    file_list = []
    try:
        all_file = os.listdir(catalog_path)
    except FileNotFoundError:
        return ''
    for file_name in all_file:
        file_dict = {}
        file_path = '{}/{}'.format(catalog_path, file_name)
        file = os.stat(file_path)
        file_dict['file_name'] = file_name
        file_dict['file_size'] = get_size(file.st_size)
        file_dict['file_time'] = get_time(file.st_mtime)
        file_list.append(file_dict)
    return file_list


def get_size(size):
    size = int(size)
    if size < 1000:
        return '{}b'.format(size)
    elif size < 1000000:
        return '{}kb'.format(round(size/1000, 1))
    else:
        return '{}M'.format(round(size/1000000, 1))


def get_time(t):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t))
