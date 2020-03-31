# -*- coding: utf-8 -*-
# @Time     : 2019/11/18 19:13
# @Author   : Run 
# @File     : mp4.py
# @Software : PyCharm


from urllib import request
from tqdm import tqdm
import os
from random import randint


class Downloader:
    """适用于从下载链接获取内容，格式不限。非并行，速度非常慢"""
    def __init__(self, output='movies/'):
        self.output_folder = output
        if not os.path.exists(output):
            os.mkdir(output)

        self.bar = None
        self.total_size = None
        self.process = 0  # 进度条进度

    def reset(self):
        self.bar = None
        self.total_size = None
        self.process = 0  # 进度条进度

    def schedule(self, a, b, c):
        if self.total_size is None:
            total_size = c / 1024 ** 2
            if total_size >= 1024:
                self.total_size = '{}G'.format(round(total_size / 1024, 2))
            else:
                self.total_size = '{}M'.format(round(total_size, 2))
        finished_size = min(c, a * b) / 1024 ** 2
        if finished_size >= 1024:
            finished_size = '{}G'.format(round(finished_size / 1024, 2))
        else:
            finished_size = '{}M'.format(round(finished_size, 2))
        per = min(100 * a * b / c, 100)
        if self.bar is None:
            self.bar = tqdm(total=100)
        self.bar.update(int(per) - self.process)
        self.bar.set_postfix(total=self.total_size, finished=finished_size)
        self.process = int(per)

    def download(self, download_link, file_name, suffix='mp4'):
        print('video_title: {}'.format(file_name))
        try:
            file_name += '_' + str(randint(0, 1000000)) + '.' + suffix
            file_path = os.path.join(self.output_folder, file_name)
            request.urlretrieve(url=download_link, filename=file_path, reporthook=self.schedule)
        except:
            print("[fail] download {} failed".format(suffix))
            return False
        else:
            return True


