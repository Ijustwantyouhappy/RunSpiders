# -*- coding: utf-8 -*-
# @Time     : 2019/8/19 17:00
# @Author   : Run 
# @File     : jav.py
# @Software : PyCharm

from RunSpiders.video.base.m3u8 import *
from RunSpiders.utils import *
import re
from urllib.parse import urljoin


class JAV:
    """
    designed for JAV, might could also be used for other hls webs
    """
    def __init__(self, output='movies/'):
        self.downloader = M3U8Spider(output=output)

    def download_movie(self, play_url, timeout=10, retry=3):
        """

        :param play_url: 播放页地址
        :param timeout:
        :param retry:
        :return:
        """
        flag, req = request_url(play_url, timeout, retry)
        if not flag:
            print('failed crawl play_url: {}'.format(play_url))
            return False
        try:
            init_m3u8_url = re.findall("https://.+?index\.m3u8", req.text)[0]
            file_name = re.search(b'<div class="screen_wapper"(.*?)<h1 class="h1">(.*?)</h1>', req.content, re.S).\
                groups()[1].decode().strip()  # todo might be wrong
            file_name = re.sub('\t', '', file_name)
        except:
            print("can't parse m3u8_url and file_name")
            return False
        flag, req = request_url(init_m3u8_url, timeout, retry)
        if not flag:
            print('failed crawl m3u8_url: {}'.format(init_m3u8_url))
            return False
        text = req.text.strip()
        if text.endswith('index.m3u8'):
            real_m3u8_url = urljoin(init_m3u8_url, text.split('\n')[-1].strip())
            self.downloader.download_movie(real_m3u8_url, file_name)
        else:  # already been real m3u8 url
            self.downloader.download_movie(init_m3u8_url, file_name)
        self.downloader.reset()

    def download_movies(self, play_url_list, timeout=10, retry=3):
        """

        :param play_url_list:
        :param timeout:
        :param retry:
        :return:
        """
        for play_url in play_url_list:
            print(play_url)
            self.download_movie(play_url, timeout, retry)
            print("-" * 100)


# if __name__ == "__main__":
#     spider = JAV("F:/movies")
#     play_url_list = [
#         'https://nyg28.com/1/1040.html',  # need to concat real_m3u8_url according to init_m3u8_url and parse key
#         'https://nyg28.com/1/29313.html'  # init_m3u8_url is real_m3u8_url
#     ]
#     spider.download_movies(play_url_list)
