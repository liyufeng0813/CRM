# !/usr/bin/python3
# -*- coding:utf-8 -*- 

import random
import string


def get_random_str():
    random_str = random.sample(string.ascii_lowercase + string.ascii_uppercase + string.digits, 8)
    return ''.join(random_str)
