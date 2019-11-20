# -*- coding: utf-8 -*-
# @Time     : 2019/5/17 14:03
# @Author   : Run 
# @File     : __init__.py
# @Software : PyCharm

import os
from jinja2 import Environment, FileSystemLoader
# import warnings;warnings.filterwarnings("ignore")

_PATH = os.path.dirname(os.path.realpath(__file__))
# print(_PATH)
_ENV = Environment(loader=FileSystemLoader(_PATH))
