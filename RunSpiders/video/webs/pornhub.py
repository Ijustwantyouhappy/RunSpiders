# -*- coding: utf-8 -*-
# @Time     : 2019/11/17 15:40
# @Author   : Run 
# @File     : pornhub.py
# @Software : PyCharm

"""
References:
    1. [我写了个 Chrome 插件，一键下载 Pornhub 视频！](https://blog.csdn.net/weixin_40787712/article/details/103082263)

todo 寻找多线程下载mp4的方式
todo 建立错误代码表
todo 添加vps相关代码
todo 更换代理，防止被封 difficult
"""


from RunSpiders.video.base.m3u8 import *
from RunSpiders.video.base.mp4 import *
from bs4 import BeautifulSoup
import js2py
# from selenium import webdriver
import time
from prettytable import PrettyTable


class PornHub:
    """
    designed for PornHub （需要翻墙）
    """
    def __init__(self, output='movies/', mp4_switch=False, timeout=10, retry=3, sleep_interval=3):
        self.hls_downloader = M3U8Spider(output=output)
        self.mp4_downloader = Downloader(output=output)
        self.mp4_switch = mp4_switch  # 目前通过MP4下载地址下载视频速度太过缓慢，不开启该方式

        self.timeout = timeout
        self.retry = retry
        self.sleep_interval = sleep_interval

    def download_movie(self, play_url: str):
        """

        :param play_url: 播放页地址
        :param timeout:
        :param retry:
        :return:
        """
        # fetch target js codes from web page content
        flag, req = request_url(play_url, self.timeout, self.retry)
        if not flag:
            print('[fail] failed crawl play_url: {}'.format(play_url))
            return False
        if 'Sorry, but this video is private' in req.text:
            print("[fail] might be private video")
            return False
        try:
            soup = BeautifulSoup(req.content, 'lxml')
            text = soup.find('div', attrs={'id': 'player', 'class': 'original mainPlayerDiv'})\
                       .find('script', attrs={'type': "text/javascript"}).text
            pos = text.index('loadScriptUniqueId')
            s = text[:pos].strip()
            var_name = re.findall('var (flashvars_\d+) =', s)[0]
        except:
            # 有时候频繁爬取可能会导致网站返回的内容不对，不是脚本的问题，重新爬取即可
            print("[fail] can't parse play_url's content")
            return False

        # fetch video details by executing js codes
        # method1: module `execjs`
        # js = execjs.compile(s)
        # d = js.eval(var_name)
        # method2: module `js2py`
        try:
            d = js2py.eval_js(s + '\n' + var_name)
            # print(d)
            file_name = d['video_title'].strip()
            details = list(d['mediaDefinitions'])
            details = sorted(details[:-1], key=lambda x: int(x['quality']), reverse=True)
            # print(details)
        except:
            print("[fail] executing js wrong")
            return False

        init_m3u8_url, hls_quality = None, None
        mp4_url, mp4_quality = None, None
        try:
            for detail in details:
                if detail['format'] == 'mp4':
                    if mp4_url is None:
                        mp4_url = detail['videoUrl']
                        mp4_quality = detail['quality']
                elif detail['format'] == 'hls':
                    if init_m3u8_url is None:
                        init_m3u8_url = detail['videoUrl']
                        hls_quality = detail['quality']
                        break
        except:
            print("[fail] unexpected format of mediaDefinitions")
            return False

        if init_m3u8_url is not None:
            print("init_m3u8_url: {}".format(init_m3u8_url))
            flag, req = request_url(init_m3u8_url, self.timeout, self.retry)
            if not flag:
                print('[fail] failed crawl init_m3u8_url: {}'.format(init_m3u8_url))
                return False
            lines = req.text.strip().split('\n')
            for line in lines:
                if re.search('index.*m3u8', line):
                    real_m3u8_url = urljoin(init_m3u8_url, line.strip())
                    break
            else:
                print("[fail] can't find real_m3u8_url")
                return False
            print("real_m3u8_url: {}".format(real_m3u8_url))
            print("video_quality: {}P".format(hls_quality))
            flag = self.hls_downloader.download_movie(real_m3u8_url, file_name)
            self.hls_downloader.reset()
            return flag
        else:
            if mp4_url is not None:
                print("can't find m3u8_url")
                print("mp4_url: {}".format(mp4_url))
                print("video_quality: {}P".format(mp4_quality))
                if self.mp4_switch:
                    flag = self.mp4_downloader.download(mp4_url, file_name)
                    self.mp4_downloader.reset()
                    return flag
                else:
                    print("[fail] mp4' switch has been turned off.")
                    return False
            else:
                print("[fail] can't find any video_url from mediaDefinitions")
                return False

    def download_movies(self, play_url_list: list) -> list:
        """

        :param play_url_list:
        :return: fail_url_list
        """
        play_url_set = set(re.sub(r'&pkey=\d+', '', url) for url in play_url_list)
        total_num = len(play_url_set)
        print("videos: {}".format(total_num))
        print("-" * 100)

        fail_list = []
        for ind, play_url in enumerate(play_url_set, 1):
            print("index: {}".format(ind))
            print("play_url: {}".format(play_url))
            if not self.download_movie(play_url):
                fail_list.append(play_url)
            print("-" * 100)

        fail_num = len(fail_list)
        success_num = total_num - fail_num
        table = PrettyTable()
        table.field_names = ['total', 'success', 'fail']
        table.add_row([total_num, success_num, fail_num])
        print(table)
        print("-" * 100)
        # print("fail:")
        # print(fail_list)
        return fail_list

    def fetch_video_urls_from_playlist(self, playlist_url: str) -> list:
        """
        异步加载:
            method1. solved by selenium, 有时候不起作用。[deprecated]
            method2. F12 - XHR，找到了请求的接口。
        todo 播单页面内有视频总数的信息，但好像不一定准。
        :param playlist_url: 播放列表地址
        :return: 视频播放地址列表
        """
        print("playlist_url: {}".format(playlist_url))
        # get playlist_id
        try:
            playlist_id = re.findall('playlist/(\d+)', playlist_url)[0]
            print("playlist_id: {}".format(playlist_id))
        except:
            print("[fail] can't get playlist's id from url")
            return []

        # method1: by selenium [deprecated]
        # try:
        #     option = webdriver.ChromeOptions()
        #     option.add_argument('headless')
        #     driver = webdriver.Chrome(options=option)
        #     driver.get(playlist_url)
        #     print("selenium started")
        # except:
        #     print("selenium won't work")
        #
        # try:
        #     i = 1
        #     height = driver.execute_script("return document.body.scrollHeight;")  # 当前页面的最大高度
        #     while True:
        #         driver.execute_script("scroll(0,100000)")  # 执行拖动滚动条操作
        #         time.sleep(sleep_interval)
        #         new_height = driver.execute_script("return document.body.scrollHeight;")
        #         print("scroll: {}, height: {}".format(i, new_height))
        #         i += 1
        #         if new_height == height and i > 5:
        #             break
        #         else:
        #             height = new_height
        # except:
        #     print("异步加载处理报错")
        #
        # try:
        #     videos = BeautifulSoup(driver.page_source, 'lxml') \
        #         .find('div', attrs={'class': 'container playlistSectionWrapper'}) \
        #         .find_all('span', attrs={'class': 'title'})
        # except:
        #     print("can't parse page_source")
        #
        # driver.close()

        # method2 post requests by api
        s = requests.Session()
        try:
            req = s.get(playlist_url, timeout=self.timeout)
            videos = BeautifulSoup(req.content, 'lxml') \
                .find('div', attrs={'class': 'container playlistSectionWrapper'}) \
                .find_all('span', attrs={'class': 'title'})
        except:
            print("[fail] request playlist_url failed")
            return []
        start_num = len(videos)
        if start_num == 0:
            print("[fail] request playlist_url successfully but get nothing")
            return []
        else:
            print("page: 1. videos: {}".format(start_num))

        page = 2
        items_per_page = 40  # todo might can be changed?
        while True:
            try:
                req = s.get('https://www.pornhub.com/playlist/viewChunked?id={}&offset={}&itemsPerPage={}'.
                            format(playlist_id, start_num, items_per_page), timeout=self.timeout)
                time.sleep(self.sleep_interval)  # todo might be unnecessary
                new_videos = BeautifulSoup(req.content, 'lxml').find_all('span', attrs={'class': 'title'})
            except:
                print("[fail] request page {} failed".format(page))
                break
            if len(new_videos) == 0:
                break
            else:
                print("page: {}. videos: {}".format(page, len(new_videos)))
                videos += new_videos
                start_num += items_per_page
                page += 1

        play_url_list = [urljoin('https://www.pornhub.com/', x.a['href']) for x in videos]

        return play_url_list

    def download_playlist(self, playlist_url: str) -> list:
        """

        :param playlist_url: 播放列表地址
        :return:
        """
        play_url_list = self.fetch_video_urls_from_playlist(playlist_url)
        fail_list = self.download_movies(play_url_list)
        return fail_list

    def download_playlists(self, playlists: list) -> list:
        """
        一次性下载多个播放列表
        :param playlists:
        :return:
        """
        playlists = set(playlists)
        print("playlists: {}\n".format(len(playlists)))
        videos = []
        for playlist_url in playlists:
            new_videos = self.fetch_video_urls_from_playlist(playlist_url)
            print("total videos: {}\n".format(len(new_videos)))
            videos += new_videos
        fail_list = self.download_movies(videos)

        return fail_list

    def _parse_anyone_url(self, url=None, category=None, name=None):
        if url is not None:
            res = re.findall('/(users|pornstar|model)/(.*?)/', url + '/')  # todo 可能还会有其他账户类型
            if len(res) == 0:
                print("[fail] can't parse url: {}".format(url))
                return None, None, None
            category, name = res[0]
        videos_url = 'https://www.pornhub.com/{}/{}/videos'.format(category, name)
        return category, name, videos_url

    def _fetch_model_videos_urls(self, url=None, name=None):
        """
        目前发现共有upload（也即free）和paid两部分，paid中并不都是付费的，所以也有爬取的价值。
            paid的视频是通过load more的按键加载，是增量的形式，通过ajax爬取；
            而upload的则是通过page按钮翻页，也有可能仅有一页所以没有page按钮。
        :param url:
        :param name:
        :return:
        """
        _, _, videos_url = self._parse_anyone_url(url=url, category='model', name=name)
        if videos_url is None:
            return
        print("model's videos_url: {}".format(videos_url))
        play_url_list = []

        # part1: paid
        paid_url = videos_url + '/paid'
        s = requests.Session()
        try:
            req = s.get(paid_url, timeout=self.timeout)
            videos = BeautifulSoup(req.content, 'lxml') \
                .find('div', attrs={'class': 'videoUList'}) \
                .find_all('div', attrs={'class': 'thumbnail-info-wrapper clearfix'})
        except:
            print("[fail] request paid videos failed")
            videos = []
        else:
            start_num = len(videos)
            if start_num > 0:
                print("paid page: 1. videos: {}".format(start_num))
                # load more
                page = 2
                while True:
                    try:
                        page_url = '{}/ajax?o=best&page={}'.format(paid_url, page)
                        req = s.get(page_url, timeout=self.timeout)
                        time.sleep(self.sleep_interval)  # todo might be unnecessary
                        new_videos = BeautifulSoup(req.content, 'lxml')\
                            .find_all('div', attrs={'class': 'thumbnail-info-wrapper clearfix'})
                    except:
                        print("[fail] request paid videos page {} failed".format(page))
                        break
                    if len(new_videos) == 0:
                        break
                    else:
                        print("paid page: {}. videos: {}".format(page, len(new_videos)))
                        videos += new_videos
                        page += 1
        # filter
        for video in videos:
            play_url = urljoin('https://www.pornhub.com/', video.find('a')['href'])
            price = video.find('span', attrs={'class': 'price'})
            if price is None:
                play_url_list.append(play_url)
        print("paid vedios: {}, without a price: {}".format(len(videos), len(play_url_list)))

        # part2: free
        free_url = videos_url + '/upload'
        try:
            req = s.get(free_url, timeout=self.timeout)
            soup = BeautifulSoup(req.content, 'lxml')
            videos = soup.find('div', attrs={'class': 'videoUList'})\
                .find_all('div', attrs={'class': 'thumbnail-info-wrapper clearfix'})
        except:
            print("[fail] request free videos failed")
            videos = []
        else:
            more_pages = soup.find('div', attrs={'class': 'pagination3'})
            if more_pages:  # 有page按钮，说明有更多page
                start_num = len(videos)
                if start_num > 0:
                    print("free page: 1. videos: {}".format(start_num))
                    # more pages
                    page = 2
                    while True:
                        try:
                            page_url = '{}?page={}'.format(free_url, page)
                            req = s.get(page_url, timeout=self.timeout)
                            time.sleep(self.sleep_interval)  # todo might be unnecessary
                            new_videos = BeautifulSoup(req.content, 'lxml')\
                                .find('div', attrs={'class': 'videoUList'}) \
                                .find_all('div', attrs={'class': 'thumbnail-info-wrapper clearfix'})
                        except:
                            print("[fail] request free videos page {} failed".format(page))
                            break
                        if len(new_videos) == 0:
                            break
                        else:
                            print("free page: {}. videos: {}".format(page, len(new_videos)))
                            videos += new_videos
                            page += 1
        free_videos_url_list = [urljoin('https://www.pornhub.com/', video.find('a')['href']) for video in videos]
        print("free videos: {}".format(len(free_videos_url_list)))

        play_url_list += free_videos_url_list
        play_url_list = list(set(play_url_list))
        print("total videos: {}".format(len(play_url_list)))
        return play_url_list

    def download_model_videos(self, url=None, name=None):
        """
        [unrecommended] 建议使用函数download_anyone_videos
        :param url:
        :param name:
        :return:
        """
        play_url_list = self._fetch_model_videos_urls(url, name)
        fail_list = self.download_movies(play_url_list)
        return fail_list

    def download_users_videos(self, url=None, name=None):  # todo
        _, _, videos_url = self._parse_anyone_url(url=url, category='users', name=name)
        if videos_url is None:
            return

    def download_pornstar_videos(self, url=None, name=None):  # todo
        _, _, videos_url = self._parse_anyone_url(url=url, category='pornstar', name=name)
        if videos_url is None:
            return

    def download_anyone_videos(self, url):
        # todo 待完善
        category, name, videos_url = self._parse_anyone_url(url)
        if category == 'users':
            fail_list = self.download_users_videos(videos_url)
        elif category == 'model':
            fail_list = self.download_model_videos(videos_url)
        elif category == 'pornstar':
            fail_list = self.download_pornstar_videos(videos_url)
        else:
            return []
        return fail_list


if __name__ == "__main__":
    spider = PornHub("F:/movies")

    # play_url_list = []
    # fail_list = spider.download_movies(play_url_list)
    # print(fail_list)

    # playlists = []
    # fail_list = spider.download_playlists(playlists)
    # print(fail_list)

    # users/model/pornhub
    # url = ''
    # fail_list = spider.download_anyone_videos(url)
    # print(fail_list)



