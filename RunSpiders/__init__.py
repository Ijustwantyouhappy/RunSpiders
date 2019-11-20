# -*- coding: utf-8 -*-
# @Time     : 2019/5/16 16:49
# @Author   : Run
# @File     : __init__.py
# @Software : PyCharm

"""
todo:
    1. 探索`gevent`。`monkey.patch_all()`总是导致运行`from RunSpiders import *`时出现错误
        `RuntimeError: cannot release un-acquired lock`
    2. logging模块
"""


from RunSpiders.utils import Checker
from RunSpiders.book.web_fiction import WebFictionSpider
from RunSpiders.others.for_github import get_popularity_info


__version__ = "1.0.7"


checker = Checker()
checker.main()
