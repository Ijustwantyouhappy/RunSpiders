# -*- coding: utf-8 -*-
# @Time     : 2019/10/20 17:28
# @Author   : Run 
# @File     : vk.py
# @Software : PyCharm

"""
todo 寻找接口，使得使用更方便，目前需要自己在开发者工具中确定m3u8_url
"""

from RunSpiders.video.base.m3u8 import *


class VK:
    """
    designed for VK
    """
    def __init__(self, output='movies/'):
        self.downloader = M3U8Spider(output=output)

    def download_movie(self, file_name, m3u8_url):
        self.downloader.download_movie(m3u8_url, file_name)
        self.downloader.reset()

    def download_movies(self, movies):
        """

        :param movies: list of tuple. [(file_name, m3u8_url), ...]
        :return:
        """
        for file_name, m3u8_url in movies:
            print(file_name)
            print(m3u8_url)
            self.download_movie(file_name, m3u8_url)
            print("-" * 100)