# -*- coding: utf-8 -*-
# @Time     : 2019/5/14 17:55
# @Author   : Run 
# @File     : web_fiction.py
# @Software : PyCharm

"""
references:
    1. [API documentation for recipes](https://manual.calibre-ebook.com/news_recipe.html#calibre.web.feeds.news.BasicNewsRecipe)
    2. [ebook-convert](https://manual.calibre-ebook.com/generated/en/ebook-convert.html)

todo
    1. ebook-convert 在python console和Run中运行时输出信息会乱码，只有在命令行调用时才能正常显示
    2. ebook-convert 爬虫太慢，考虑自写，寻找生成mobi格式的工具
    4. use python package `python-fire` automatically generating command line interfaces
    5. 分卷 volume 卷名
    6. 分析每本书下载情况，缺失章节补全等
    7. 增加fail_list

notes:
    1. os.sys(command) 将输出屏显，在Pycharm中Settings > Editor > File Encodings将编码切换至GBK可解决中文显示乱码；
       file = os.popen(command)，通过file.read()读取输出内容时，才会开始执行命令
"""

from RunSpiders.utils import *
from RunSpiders.templates import _ENV

import sys
import requests
from urllib.parse import urljoin
import re
from bs4 import BeautifulSoup
import os
import warnings; warnings.filterwarnings("ignore")
# from ebooklib import epub


class WebFictionSpider:

    def __init__(self, output="ebooks/", simultaneous_downloads=30, sub_spider_list=None):
        """

        :param output: 电子书文件存放路径
        :param simultaneous_downloads: 多线程下载的线程数
        :param sub_spider_list: 指定网站爬虫类. e.g. [SubSpider1, SubSpider2]
        """
        if sub_spider_list is None:
            self.spiders_list = [
                SubSpider1(simultaneous_downloads),
                # SubSpider2(simultaneous_downloads),
                # SubSpider3(simultaneous_downloads)
                SubSpider7(simultaneous_downloads),
                SubSpider9(simultaneous_downloads)
            ]  # todo 检验网站是否可访问
        else:
            self.spiders_list = [spider(simultaneous_downloads) for spider in sub_spider_list]
        self.book_folder = output
        if not os.path.exists(output):
            os.makedirs(output)
        #
        self.spider_books_list = []  # [(spider, [(book, author, url), ...]), ...]
        self.recipes_list = []

    def reset(self):
        self.spider_books_list = []
        self.recipes_list = []

    def search(self, book=None, author=None, target="one"):
        """

        :param book: 书名
        :param author: 作者名
        :param target:
            one: 在某个网站有搜到至少一本符合要求的书籍即停止
            all: 遍历所有网站，搜集所有符合要求的书籍
        :return: bool
        """
        if book is None and author is None:
            raise Exception("please input book name or author name")

        if target == "one":
            for spider in self.spiders_list:
                print("search {}, {}".format(spider.name, spider.url))
                res_list = spider.search(book, author)
                print('-' * 100)
                if len(res_list) > 0:
                    self.spider_books_list.append((spider, res_list[:1]))
                    return True
        elif target == "all":
            for spider in self.spiders_list:
                print("search {}, {}".format(spider.name, spider.url))
                res_list = spider.search(book, author)
                print("-" * 100)
                if len(res_list) > 0:
                    self.spider_books_list.append((spider, res_list))
            if len(self.spider_books_list) > 0:
                return True
        else:
            pass

        return False

    def gen_recipes(self, exclude_books=None):
        """

        :param exclude_books: 指定books不下载
        :return: bool
        """
        if len(self.spider_books_list) == 0:
            return False

        for spider, tmp in self.spider_books_list:
            for sub_tmp in tmp:
                if exclude_books is not None and sub_tmp[0] in exclude_books:
                    continue
                recipe = spider.gen_recipe(*sub_tmp, self.book_folder)
                if recipe is not None:
                    self.recipes_list.append(recipe)

        return True

    def recipe_to_ebook(self, recipe, ebook_format='mobi'):
        """
        convert recipe to ebook, save in self.book_folder
        :param recipe: e.g. ebooks/1.recipe
        :param ebook_format: epub, mobi, ... (kindle usually use mobi)
        :return:
        :notes:
            1. make sure you have installed calibre and add `ebook-convert` to environment variables
        """
        # if not check_calibre_installed():  # test ebook-convert command
        #     return
        if not os.path.exists(recipe):
            print("can't find recipe: {}".format(recipe))
            return

        recipe_name = os.path.basename(recipe)  # 书名_作者.recipe
        if not recipe_name.endswith('.recipe'):
            print("invalid recipe name: {}".format(recipe_name))
            return
        name = recipe_name.replace('.recipe', '')
        title, author = name.split('_')

        # check exists
        ebook_name = name + '.' + ebook_format
        target_ebook = os.path.join(self.book_folder, ebook_name)
        if os.path.exists(target_ebook):
            print("{} already exists in folder {}".format(ebook_name, self.book_folder))
            return

        # convert
        print("generate {}".format(ebook_name))
        try:
            os.system('ebook-convert "{}" "{}" --title "{}" --authors "{}"'.format(recipe, target_ebook, title, author))
        except Exception as e:
            print("convert ebook failed: {}".format(e))

    def gen_ebooks(self, delete_recipes=True):
        """
        convert recipes to ebooks
        :param delete_recipes:
        :return:
        """
        if len(self.recipes_list) == 0:
            return

        # test ebook-convert command
        if not Checker().check_calibre():
            return

        # convert
        for recipe in self.recipes_list:
            self.recipe_to_ebook(recipe)
            if delete_recipes:
                os.remove(recipe)

    def download(self, book=None, author=None, exclude_books=None):
        """
        下载指定书籍或者指定作者的所有书
        :param book: 如果传入书名，则只下载该书
        :param author: 如果传入作者名，则下载该作者能搜索到的所有不重名书籍
        :param exclude_books: 当指定author想要下载其所有作品时，可传入该参数指定books不下载
        :return:
        """
        if book is not None:
            target = "one"
        elif author is not None:
            target = "all"
        else:
            print("please input book or author")
            return

        self.search(book, author, target)
        self.gen_recipes(exclude_books)
        self.gen_ebooks()
        self.reset()
        print('\n\n')

    def download_books(self, book_list):
        """

        :param book_list:
        :return:
        """
        for book in book_list:
            print("title: {}".format(book).center(100))
            print("-" * 100)
            self.download(book)


class CoverSpider:

    def search(self, book, author=None):
        web_funcs = [
            self.search_qidian,
            self.search_zongheng
        ]
        for func in web_funcs:
            img_url = func(book, author)
            if img_url is not '':
                return img_url

        return ''

    def download(self, url, filename='cover.jpg'):
        with open(filename, 'wb') as file:
            file.write(requests.get(url).content)

    def search_qidian(self, book, author=None):
        web_name = '起点中文网'
        web_url = 'https://www.qidian.com'
        search_url = '{}/search?kw={}'.format(web_url, book)
        #
        flag, req = request_url(search_url)
        if not flag:
            print("book: {}, author: {}. requests {} failed".format(book, author, web_name))
            return ''
        try:
            soup = BeautifulSoup(req.content, 'lxml')
            div = soup.find('div', attrs={'class': 'book-img-text'})
            lis = div.find_all('li')
            for li in lis:
                book0 = li.find('h4').string.strip()
                if book0 == book:
                    if author is not None:
                        author0 = li.find('p', {'class': 'author'}).find('a').string.strip()
                        if author != author0:
                            continue
                    src = 'http:' + re.sub('/150$', '', li.find('img')['src'])  # todo
                    return src
        except:
            print("book: {}, author: {}. parse {}'s page failed".format(book, author, web_name))

        return ''

    def search_zongheng(self, book, author=None):
        web_name = '纵横中文网'
        web_url = 'http://www.zongheng.com/'
        search_url = 'http://search.zongheng.com/s?keyword={}'.format(book)
        #
        flag, req = request_url(search_url)
        if not flag:
            print("book: {}, author: {}. requests {} failed".format(book, author, web_name))
            return ''
        try:
            soup = BeautifulSoup(req.content, 'lxml')
            divs = soup.find_all('div', attrs={'class': 'search-result-list clearfix'})
            for div in divs:
                book0 = div.find('h2', attrs={'class': 'tit'}).find('a').text.strip()
                if book0 == book:
                    if author is not None:
                        author0 = div.find('div', attrs={'class': 'bookinfo'}).find('a').string.strip()
                        if author != author0:
                            continue
                    src = div.find('div', attrs={'class': 'imgbox fl se-result-book'}).find('img')['src']
                    return src
        except:
            print("book: {}, author: {}. parse {}'s page failed".format(book, author, web_name))

        return ''


class SubSpider:
    """针对每个小说网站的爬虫策略原型"""

    def __init__(self):
        self.url = ''
        self.name = ''
        self.template = ''  # 模板文件

    def search(self, book=None, author=None):
        """

        :param book:
        :param author:
        :return: [(book, author, index_url, cover_url), ...]
        """

        # search
        # parse
        # filter
        pass

    def gen_recipe(self, book, author, index_url, cover_url, folder="ebooks"):
        """

        :param book:
        :param author:
        :param index_url: 索引页地址，不能为空
        :param cover_url: 可以为空，不能成功下载封面图片
        :param folder:
        :return:
        """
        pass


class SubSpider1:

    def __init__(self, simultaneous_downloads=30):
        self.url = 'https://www.xbiquge6.com'
        self.name = '新笔趣阁'
        self.template = "novel_template1.recipe"
        self.simultaneous_downloads = simultaneous_downloads
        self.cover_spider = CoverSpider()

    def search(self, book=None, author=None):
        """
        1. 该网站仅允许一个关键词，所以当书名和作者名均传入时以书名为搜索关键词，但两者都会作为对搜索结果的筛选条件；
        2. 该网页的查询结果会分页展示
        :param book:
        :param author:
        :return: [(book, author, index_url, cover_url), ...]
        """
        keyword = book if book is not None else author

        # 第一页
        url = self.url + "/search.php?keyword={}".format(keyword)
        flag, req = request_url(url, timeout=10, retry=1)
        if flag:
            soup = BeautifulSoup(req.content, "lxml")
            if '末页' in req.text:  # 搜索结果不止一页
                total_num = int(re.findall('page=(\d+)', soup.find('a', attrs={'title': '末页'})['href'])[0])
            else:
                total_num = 1
            books = soup.find_all('div', attrs={'class': "result-item result-game-item"})
        else:
            books = []
            total_num = 0
        print("page 1 parsed, {} book(s) found".format(len(books)))
        # 后续页
        for page in range(2, total_num + 1):
            new_url = url + "&page={}".format(page)
            flag, req = request_url(new_url, timeout=10, retry=1)
            if flag:
                soup = BeautifulSoup(req.content, "lxml")
                new_books = soup.find_all('div', attrs={'class': "result-item result-game-item"})
                books += new_books
                print("page {} parsed, {} book(s) found".format(page, len(new_books)))
            else:
                print("[fail] page {} parsed".format(page))
        #
        print('search {} page(s), find {} book(s)'.format(total_num, len(books)))
        if len(books) == 0:
            return []

        # parse
        def _parse_details(soup):
            # image_url
            try:
                img_div = soup.find('div', attrs={'class': "result-game-item-pic"})
                img_url = img_div.a.img['src']
            except:
                img_url = ''
            # book, author, index_url
            try:
                details_div = soup.find('div', attrs={'class': 'result-game-item-detail'})
                a = details_div.h3.a
                book = a['title'].strip()
                index_url = a['href']
                author = details_div.div.p.find_all('span')[1].string.strip()
                # print(book, author, url)
            except:
                return None

            return [book, author, index_url, img_url]

        #
        details_list = []
        for soup in books:
            tmp = _parse_details(soup)
            if tmp is not None:
                book0, author0, _, img_url = tmp
                if book is not None and book != book0:
                    continue
                if author is not None and author != author0:
                    continue
                # search cover image's url
                img_url = self.cover_spider.search(book0, author0)
                if img_url is not '':
                    tmp[-1] = img_url
                details_list.append(tmp)
        print('after parsing and filtering, {} book(s) left'.format(len(details_list)))

        return details_list

    def gen_recipe(self, book, author, index_url, cover_url, folder="ebooks"):
        """

        :param book:
        :param author:
        :param index_url: 索引页地址，不能为空
        :param cover_url: 可以为空，不能成功下载封面图片
        :param folder:
        :return: recipe文件路径
        """
        # check if recipe exists
        file_name = book + '_' + author + '.recipe'  # 书名_作者.recipe
        recipe = os.path.join(folder, file_name)
        if os.path.exists(recipe):
            print("{} already exists in folder {}".format(file_name, folder))
            return
        else:
            if not os.path.exists(folder):
                os.makedirs(folder)

        # fill template
        details_dict = {
            'title': book,
            'cover_url': cover_url,
            'index_url': index_url,
            'web_url': self.url,
            'simultaneous_downloads': self.simultaneous_downloads
        }
        template = _ENV.get_template(self.template)
        cont = template.render(**details_dict)

        # save
        with open(recipe, 'w', encoding="utf-8") as file:
            file.write(cont)

        return recipe


class SubSpider2:

    def __init__(self, simultaneous_downloads=30):
        self.url = 'https://www.biquge.cc'
        self.name = '笔趣阁'
        self.template = "novel_template2.recipe"
        self.simultaneous_downloads = simultaneous_downloads
        self.cover_spider = CoverSpider()

    def search(self, book=None, author=None):
        """
        该网站的搜索是通过一个接口以参数siteid传入站点名进行请求，允许多个关键词，可以同时筛选书名和作者名；
        有不少网站都是通过这个接口搜书的；
        该网页的查询结果只会有一页。
        :param book:
        :param author:
        :return: [(book, author, index_url, img_url), ...]
        """

        # search
        keyword = "+".join(filter(lambda x: x is not None, [book, author]))
        url = "https://sou.xanbhx.com/search?siteid=biqugecc&q={}".format(keyword)
        flag, req = request_url(url, verify=False)
        if flag:
            cont = req.content
            soup = BeautifulSoup(cont, "lxml")
            books_list = soup.find('ul').find_all('li')[1:]
            print('find {} book(s)'.format(len(books_list)))
            if len(books_list) == 0:
                return []
        else:
            print("request search_url failed")
            return []

        # parse
        def _parse_details(soup):
            # image_url
            img_url = ""  # todo
            # book, author, index_url
            try:
                a = soup.find('span', attrs={'class': 's2'}).a
                book = a.text.strip()
                index_url = a['href']
                author = soup.find('span', attrs={'class': 's4'}).text.strip()
                # print(book, author, url)
            except:
                return None

            return [book, author, index_url, img_url]

        #
        details_list = []
        for soup in books_list:
            tmp = _parse_details(soup)
            if tmp is not None:
                book0, author0, _, _ = tmp
                if book is not None and book != book0:
                    continue
                if author is not None and author != author0:
                    continue
                # search cover image's url
                img_url = self.cover_spider.search(book0, author0)
                if img_url is not '':
                    tmp[-1] = img_url
                details_list.append(tmp)
        print('after parsing and filtering, {} book(s) left'.format(len(details_list)))

        return details_list

    def gen_recipe(self, book, author, index_url, cover_url, folder="recipes"):
        """

        :param book:
        :param author:
        :param index_url: 索引页地址，不能为空
        :param cover_url: 可以为空，不能成功下载封面图片
        :param folder:
        :return: recipe文件路径
        """
        # check if recipe exists
        file_name = book + '_' + author + '.recipe'  # 书名_作者.recipe
        recipe = os.path.join(folder, file_name)
        if os.path.exists(recipe):
            print("{}  already exists in folder {}".format(file_name, folder))
            return
        else:
            if not os.path.exists(folder):
                os.makedirs(folder)

        # fill template
        details_dict = {
            'title': book,
            'cover_url': cover_url,
            'index_url': index_url,
            'web_url': index_url,
            'simultaneous_downloads': self.simultaneous_downloads
        }
        template = _ENV.get_template(self.template)
        cont = template.render(**details_dict)

        # save
        with open(recipe, 'w', encoding="utf-8") as file:
            file.write(cont)

        return recipe


class SubSpider3:
    # [deprecated] 该网站反爬虫策略太严格，需要带cookie访问，访问速度太快还会被封
    def __init__(self, simultaneous_downloads=30):
        self.url = 'https://www.kuaiyankanshu.net/'
        self.name = '快眼看书'
        self.template = "novel_template3.recipe"
        self.simultaneous_downloads = simultaneous_downloads
        self.headers = self.get_headers()

    def get_headers(self):
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
            'referer': self.url,
            'content-type': 'text/html; charset=utf-8',
            'cookie': get_cookie_by_selenium(self.url)
        }
        return headers

    def search(self, book=None, author=None):
        """
        该网站参数：
            - searchtype 搜索类型
                * author: 按作者搜索
                * novelname: 按书名搜索
            - searchkey 关键词
        该网页的查询结果只会有一页
        :param book:
        :param author:
        :return: [(book, author, index_url, img_url), ...]
        """
        # search
        if book is not None:
            url = '{}search/result.html?searchtype=novelname&searchkey={}'.format(self.url, book)
        elif author is not None:
            url = '{}search/result.html?searchtype=author&searchkey={}'.format(self.url, author)
        else:
            print("author and book can't be `None` in the same time")
            return []
        flag, req = request_url(url, headers=self.headers)
        if flag:
            cont = req.content
            soup = BeautifulSoup(cont, "lxml")
            books_list = soup.find('ul', {'class': 'librarylist'}).find_all('li')
            print('find {} book(s)'.format(len(books_list)))
            if len(books_list) == 0:
                return []
        else:
            print("request search_url failed")
            return []

        # parse
        def _parse_details(soup):
            try:
                spans = soup.find('p', {'class': 'info'}).find_all('span')
                book = spans[0].a['title'].strip()
                author = spans[1].a.string.strip()
                index_url = urljoin(self.url, spans[0].a['href']) + 'dir.html'
                img_url = urljoin("https://", soup.img['src'])
            except:
                return None

            return book, author, index_url, img_url

        #
        details_list = []
        for soup in books_list:
            tmp = _parse_details(soup)
            if tmp is not None:
                book0, author0, _, _ = tmp
                if book is not None and book != book0:
                    continue
                if author is not None and author != author0:
                    continue
                details_list.append(tmp)
        print('after parsing and filtering, {} book(s) left'.format(len(details_list)))

        return details_list

    def gen_recipe(self, book, author, index_url, cover_url, folder="recipes"):
        """

        :param book:
        :param author:
        :param index_url: 索引页地址，不能为空
        :param cover_url: 可以为空，不能成功下载封面图片
        :param folder:
        :return: recipe文件路径
        """
        # check if recipe exists
        file_name = book + '_' + author + '.recipe'  # 书名_作者.recipe
        recipe = os.path.join(folder, file_name)
        if os.path.exists(recipe):
            print("{}  already exists in folder {}".format(file_name, folder))
            return
        else:
            if not os.path.exists(folder):
                os.makedirs(folder)

        # fill template
        details_dict = {
            'title': book,
            'cover_url': cover_url,
            'index_url': index_url,
            'web_url': self.url,
            'simultaneous_downloads': self.simultaneous_downloads
        }
        template = _ENV.get_template(self.template)
        cont = template.render(**details_dict)

        # save
        with open(recipe, 'w', encoding="utf-8") as file:
            file.write(cont)

        return recipe


class SubSpider4:
    def __init__(self, simultaneous_downloads=30):
        self.url = 'https://www.biduo.cc/'
        self.name = '笔趣阁'
        self.template = "novel_template4.recipe"
        self.simultaneous_downloads = simultaneous_downloads
        self.cover_spider = CoverSpider()


class SubSpider5:
    def __init__(self, simultaneous_downloads=30):
        self.url = 'http://www.ibqg5200.com/'
        self.name = '笔趣阁5200'
        self.template = "novel_template5.recipe"
        self.simultaneous_downloads = simultaneous_downloads
        self.cover_spider = CoverSpider()


class SubSpider6:
    def __init__(self, simultaneous_downloads=30):
        self.url = 'http://www.gdbzkz.com/'
        self.name = '鬼吹灯'
        self.template = "novel_template6.recipe"
        self.simultaneous_downloads = simultaneous_downloads
        self.cover_spider = CoverSpider()


class SubSpider7:
    def __init__(self, simultaneous_downloads=30):
        self.url = 'https://www.37zw.net/'
        self.name = '三七中文'
        self.template = "novel_template7.recipe"
        self.simultaneous_downloads = simultaneous_downloads
        self.cover_spider = CoverSpider()

    def search(self, book=None, author=None):
        """
        该网站参数：
            - type 搜索类型
                * author: 按作者搜索
                * articlename: 按书名搜索
            - s 关键词
        该网页的查询结果只会有一页
        :param book:
        :param author:
        :return: [(book, author, index_url, img_url), ...]
        """
        # search
        if book is not None:
            url = '{}s/so.php?type=articlename&s={}'.format(self.url, book)
        elif author is not None:
            url = '{}s/so.php?type=author&s={}'.format(self.url, author)
        else:
            print("author and book can't be `None` in the same time")
            return []
        flag, req = request_url(url)
        if flag:
            cont = req.content
            soup = BeautifulSoup(cont, "lxml")
            books_list = soup.find('div', {'class': 'novellist'}).find_all('li')
            print('find {} book(s)'.format(len(books_list)))
            if len(books_list) == 0:
                return []
        else:
            print("request search_url failed")
            return []

        # parse
        def _parse_details(soup):
            # image_url
            img_url = ''
            # book, author, index_url
            try:
                book, author = soup.text.strip().split('/')
                index_url = urljoin(self.url, soup.a['href'])
                # print(book, author, url)
            except:
                return None

            return [book, author, index_url, img_url]

        #
        details_list = []
        for soup in books_list:
            tmp = _parse_details(soup)
            if tmp is not None:
                book0, author0, _, img_url = tmp
                if book is not None and book != book0:
                    continue
                if author is not None and author != author0:
                    continue
                # search cover image's url
                img_url = self.cover_spider.search(book0, author0)
                if img_url is not '':
                    tmp[-1] = img_url
                details_list.append(tmp)
        print('after parsing and filtering, {} book(s) left'.format(len(details_list)))

        return details_list

    def gen_recipe(self, book, author, index_url, cover_url, folder="recipes"):
        """

        :param book:
        :param author:
        :param index_url: 索引页地址，不能为空
        :param cover_url: 可以为空，不能成功下载封面图片
        :param folder:
        :return: recipe文件路径
        """
        # check if recipe exists
        file_name = book + '_' + author + '.recipe'  # 书名_作者.recipe
        recipe = os.path.join(folder, file_name)
        if os.path.exists(recipe):
            print("{}  already exists in folder {}".format(file_name, folder))
            return
        else:
            if not os.path.exists(folder):
                os.makedirs(folder)

        # fill template
        details_dict = {
            'title': book,
            'cover_url': cover_url,
            'index_url': index_url,
            'simultaneous_downloads': self.simultaneous_downloads
        }
        template = _ENV.get_template(self.template)
        cont = template.render(**details_dict)

        # save
        with open(recipe, 'w', encoding="utf-8") as file:
            file.write(cont)

        return recipe


class SubSpider8:
    def __init__(self, simultaneous_downloads=30):
        self.url = 'https://www.guibuyu.org/'
        self.name = '笔趣阁'
        self.template = "novel_template8.recipe"
        self.simultaneous_downloads = simultaneous_downloads
        self.cover_spider = CoverSpider()


class SubSpider9:
    def __init__(self, simultaneous_downloads=30):
        self.url = 'http://www.ibiquge.net/'
        self.name = 'i笔趣阁'
        self.template = "novel_template9.recipe"
        self.simultaneous_downloads = simultaneous_downloads
        self.cover_spider = CoverSpider()

    def search(self, book=None, author=None):
        """
        该网页的查询结果只会有一页
        :param book:
        :param author:
        :return: [(book, author, index_url, img_url), ...]
        """
        # search
        if book is not None:
            url = '{}search.html?name={}'.format(self.url, book)
        elif author is not None:
            url = '{}search.html?name={}'.format(self.url, author)
        else:
            print("author and book can't be `None` in the same time")
            return []
        flag, req = request_url(url)
        if flag:
            cont = req.content
            soup = BeautifulSoup(cont, "lxml")
            books_list = soup.find('div', {'class': 'novelslist2'}).find_all('li')[1:]
            print('find {} book(s)'.format(len(books_list)))
            if len(books_list) == 0:
                return []
        else:
            print("request search_url failed")
            return []

        # parse
        def _parse_details(soup):
            # image_url
            img_url = ''
            # book, author, index_url
            try:
                al = soup.find_all('a')
                book = al[0].text.strip()
                author = al[1].text.strip()
                index_url = urljoin(self.url, al[0]['href'])
                # print(book, author, url)
            except:
                return None

            return [book, author, index_url, img_url]

        #
        details_list = []
        for soup in books_list:
            tmp = _parse_details(soup)
            if tmp is not None:
                book0, author0, _, img_url = tmp
                if book is not None and book != book0:
                    continue
                if author is not None and author != author0:
                    continue
                # search cover image's url
                img_url = self.cover_spider.search(book0, author0)
                if img_url is not '':
                    tmp[-1] = img_url
                details_list.append(tmp)
        print('after parsing and filtering, {} book(s) left'.format(len(details_list)))

        return details_list

    def gen_recipe(self, book, author, index_url, cover_url, folder="recipes"):
        """

        :param book:
        :param author:
        :param index_url: 索引页地址，不能为空
        :param cover_url: 可以为空，不能成功下载封面图片
        :param folder:
        :return: recipe文件路径
        """
        # check if recipe exists
        file_name = book + '_' + author + '.recipe'  # 书名_作者.recipe
        recipe = os.path.join(folder, file_name)
        if os.path.exists(recipe):
            print("{}  already exists in folder {}".format(file_name, folder))
            return
        else:
            if not os.path.exists(folder):
                os.makedirs(folder)

        # fill template
        details_dict = {
            'title': book,
            'cover_url': cover_url,
            'index_url': index_url,
            'web_url': self.url,
            'simultaneous_downloads': self.simultaneous_downloads
        }
        template = _ENV.get_template(self.template)
        cont = template.render(**details_dict)

        # save
        with open(recipe, 'w', encoding="utf-8") as file:
            file.write(cont)

        return recipe


if __name__ == "__main__":
    output = "ebooks"

    s = WebFictionSpider(output=output)
    # s.download(book="秘巫之主")
    # s.download(author="虾写")
    # s.download(author='傲无常', exclude_books=['国产英雄'])
    # s.download_books(['诡案追凶', '日出亚里斯'])
    # s.download_books(['不爽剧情毁灭者'])
    # s.download_books(['我真没想重生啊', '天降我才必有用', '变成血族是什么体验'])
    # '怪兽圈养计划', '副本公敌', '我的主神游戏'
    # s.download_books(['我真没想重生啊', '天降我才必有用'])

    # # 指定网站爬虫
    # s = WebFictionSpider(output=output, sub_spider_list=[SubSpider7], simultaneous_downloads=30)
    # s.download_books(['重生好人有好报', '综艺大导演', '生活系男神', '回眸1991'])

# if __name__ == "__main__":
#     """
#     -h, --help                                      Show help
#     -b, --book <book>                               Download book
#     -bs, --books <book1 book2 book3 ...>            Download books
#     -a, --author <author>                           Download author's all books
#     """
#
#     argvs = sys.argv
#     if argvs[1] in ['-h', '--help']:
#         print("""
#     -h, --help                                      Show help
#     -b, --book <book>                               Download book
#     -bs, --books <book1 book2 book3 ...>            Download books
#     -a, --author <author>                           Download author's all books
#     """)
#     elif argvs[1] in ['-bs', '--books']:
#         spider = WebFictionSpider()
#         spider.download_books(argvs[2:])
#     elif argvs[1] in ['-a', '--author']:
#         if len(argvs) == 3:
#             spider = WebFictionSpider()
#             spider.download(author=argvs[2])
#         elif len(argvs) == 5 and argvs[3] in ['-b', '--book']:
#             spider = WebFictionSpider()
#             spider.download(author=argvs[2], book=argvs[4])
#         else:
#             print("invalid format, use -h or --help to get help.")
#     elif argvs[1] in ['-b', '--book']:
#         if len(argvs) == 3:
#             spider = WebFictionSpider()
#             spider.download(book=argvs[2])
#         elif len(argvs) == 5 and argvs[3] in ['-a', '--author']:
#             spider = WebFictionSpider()
#             spider.download(book=argvs[2], author=argvs[4])
#         else:
#             print("invalid format, use -h or --help to get help.")
#     else:
#         print("invalid format, use -h or --help to get help.")
