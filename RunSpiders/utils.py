# -*- coding: utf-8 -*-
# @Time     : 2019/8/19 17:56
# @Author   : Run 
# @File     : utils.py
# @Software : PyCharm

"""
1. 官方文档：
    会话对象让你能够跨请求保持某些参数。
    它也会在同一个Session实例发出的所有请求之间保持cookie，期间使用urllib3的connection pooling功能。
    所以如果你向同一主机发送多个请求，底层的 TCP 连接将会被重用，从而带来显著的性能提升。
2. 以下给出的两种方式request_url和get_http_session，都能实现对失败的请求再进行retry次尝试，但整体感觉session的方式速度更快一些。
"""

import re
import requests
import requests.adapters
from selenium import webdriver
import time
import os
import stat
import shutil
import logging
import random
from platform import system
from prettytable import PrettyTable


def gen_logger(logger_name: str = None) -> logging.Logger:
    """
    generate logger by Python standard library `logging`
    todo add other handlers
    Notes:
        1. recommend a third-party module `loguru`, more powerful and pleasant
    """
    # logger
    logger = logging.getLogger(str(random.random()))  # set random name to avoid influence between different loggers
    logger.setLevel(logging.DEBUG)  # set logger's level to the lowest, logging.NOTEST will cause strange situations.
    logger.name = logger_name

    # formatter
    if logger_name is None:
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
    else:
        formatter = logging.Formatter('[%(asctime)s] [%(name)s~%(levelname)s] %(message)s', datefmt='%Y/%m/%d %H:%M:%S')

    # handlers
    # 1. print to screen
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.WARNING)
    logger.addHandler(stream_handler)
    # # 2. print to file
    # file_handler = logging.FileHandler("output.log", encoding='UTF-8', mode='w')
    # file_handler.setFormatter(formatter)
    # file_handler.setLevel(logging.DEBUG)
    # logger.addHandler(file_handler)

    return logger


def request_url(url, timeout=10, retry=3, retry_interval=0.1, **kwargs):
    """

    :param url:
    :param timeout:
    :param retry:
    :param retry_interval:
    :return:
        success: True, req
        fail: False, None
    """
    params = {'url': url, 'timeout': timeout}
    params.update(kwargs)
    while retry:
        try:
            req = requests.get(**params)
        except:
            retry -= 1
        else:
            if req.status_code == 200:
                return True, req
            else:
                retry -= 1
        time.sleep(retry_interval)

    return False, None


def get_http_session(pool_connections, pool_maxsize, max_retries):
    # todo rewrite to make parameters more flexible
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=pool_connections,
                                            pool_maxsize=pool_maxsize,
                                            max_retries=max_retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def get_cookie_by_selenium(url):
    # todo 如何自动获取cookie，selenium太慢
    option = webdriver.ChromeOptions()
    option.add_argument('headless')
    driver = webdriver.Chrome(options=option)
    # driver.set_page_load_timeout(1)
    driver.get(url)
    cookie = ';'.join(["{}={}".format(item["name"], item["value"]) for item in driver.get_cookies()])
    driver.close()

    return cookie


def delete_path(file_path: str) -> None:
    """
    Force delete file or dir(contains all subdirs and files).
    Ignore file's attributes like 'read-only'.
    This function is copied from package `RunToolkit`.
    """
    if os.path.exists(file_path):
        if os.path.isfile(file_path):  # file
            os.chmod(file_path, stat.S_IWRITE)
            os.remove(file_path)
        else:  # dir
            for path, sub_folders, sub_files in os.walk(file_path):
                for file in sub_files:
                    os.chmod(os.path.join(path, file), stat.S_IWRITE)
                    os.remove(os.path.join(path, file))
            shutil.rmtree(file_path)
        print("{} deleted".format(file_path))
    else:
        print("{} doesn't exist".format(file_path))


class Checker:
    """检查环境是否配置成功"""
    def __init__(self):
        self.system = system()  # Windows/Darwin

    def main(self):
        table = PrettyTable()
        table.field_names = ["target", "command", "pass"]

        table.add_row(['calibre', 'ebook-convert --version', self.check_calibre()])
        table.add_row(['ffmpeg', 'ffmpeg -version', self.check_ffmpeg()])
        table.add_row(['PornHub', 'ping pornhub.com', self.check_website_connection('pornhub.com')])

        table.align = 'l'
        print(table)

    def check_calibre(self) -> bool:
        """
        用于合成电子书。
        检查以下是否完成:
            1. 安装calibre
            2. `ebook-convert`命令添加至环境变量
        :return:
        """
        if self.system in {'Windows', 'Darwin'}:
            test = os.popen("ebook-convert --version")
            if 'calibre' not in test.read():
                # print("please install calibre and add ebook-convert to environment virables")
                return False
            else:
                # print('calibre installed')
                return True

    def check_ffmpeg(self) -> bool:
        """
        用于拼接ts视频片段，合成mp4文件。
        检查以下是否完成：
            1. 安装ffmpeg
            2. `ffmpeg`命令添加至环境变量
        """
        if self.system in {'Windows', 'Darwin'}:
            test = os.popen("ffmpeg -version")
            if 'ffmpeg version' in test.read():
                # print('ffmpeg installed')
                return True
            else:
                # print('please install ffmpeg and add it to environment virables')
                return False

    def check_website_connection(self, url, n=4) -> bool:
        """
        通过ping的方式检查是否能访问特定网址，主要检查能否翻墙。
        :param url:
        :param n:
        :return:
        """
        if self.system == 'Windows':
            test = os.popen("ping {} -n {}".format(url, n))
            cont = test.read()
            # print(cont)
            num = int(re.findall(r'(\d+)% .*', cont)[0])
            return num != 100
        elif self.system == 'Darwin':
            test = os.popen("ping {} -c {} -i 2".format(url, n))
            cont = test.read()
            # print(cont)
            num = float(re.findall(r'([\d\.]+)% .*', cont)[0])
            return num != 100
