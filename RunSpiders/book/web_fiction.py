# -*- coding: utf-8 -*-
# @Time     : 2019/5/14 17:55
# @Author   : Run 
# @File     : web_fiction.py
# @Software : PyCharm

"""
todo
    1. crawl cover image seperately
    2. ebook-convert 在python console和Run中运行时输出信息会乱码，只有在命令行调用时才能正常显示
    3. ebook-convert 爬虫太慢，考虑自写，寻找生成mobi格式的工具
    4. use python package `python-fire` automatically generating command line interfaces
"""

from RunSpiders.utils import *
from RunSpiders.templates import _ENV

import sys
import requests
import re
from bs4 import BeautifulSoup
import os
import warnings;warnings.filterwarnings("ignore")
# from ebooklib import epub


class WebFictionSpider:

    def __init__(self, output="ebooks/"):
        """

        :param output: 电子书文件存放路径
        """
        self.spiders_list = [
            SubSpider1(),
            SubSpider2()
        ]
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

    def gen_recipes(self):
        """

        :return: bool
        """
        if len(self.spider_books_list) == 0:
            return False

        for spider, tmp in self.spider_books_list:
            for sub_tmp in tmp:
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

    # def recipe_to_ebook_old(self, recipe, ebook_format='mobi'):
    #     """
    #     (deprecated)
    #     convert recipe to ebook, save in self.book_folder
    #         1. use ebook-convert.exe to get ebook in epub format from recipe file
    #         2. use python module `ebooklib` to edit title and author of epub ebook
    #         3. use ebook-convert.exe to convert ebook's format
    #     :param recipe: e.g. ebooks/1.recipe
    #     :param ebook_format: epub, mobi, ... (kindle usually use mobi)
    #     :return:
    #     :notes:
    #         1. make sure you have installed calibre and add `ebook-convert` to environment variables
    #     """
    #     # if not check_calibre_installed():  # test ebook-convert command
    #     #     return
    #     if not os.path.exists(recipe):
    #         print("can't find recipe: {}".format(recipe))
    #         return
    #
    #     recipe_name = os.path.basename(recipe)  # 书名_作者.recipe
    #     if not recipe_name.endswith('.recipe'):
    #         print("invalid recipe name: {}".format(recipe_name))
    #         return
    #     name = recipe_name.replace('.recipe', '')
    #     title, author = name.split('_')
    #
    #     # check exists
    #     target_ebook = os.path.join(self.book_folder, name + '.' + ebook_format)
    #     if os.path.exists(target_ebook):
    #         print("{} already exists in folder {}".format(ebook_name, self.book_folder))
    #         return
    #
    #     # .recipe -> .epub
    #     ebook_name = name + '.epub'
    #     epub_ebook = os.path.join(self.book_folder, ebook_name)
    #     if not os.path.exists(epub_ebook):
    #         print("generate {}".format(ebook_name))
    #         try:
    #             os.system('ebook-convert "{}" "{}"'.format(recipe, epub_ebook))
    #         except Exception as e:
    #             print("convert ebook failed: {}".format(e))
    #
    #     print("edit metadata")
    #     book = epub.read_epub(epub_ebook)
    #     book.set_unique_metadata('DC', 'title', title)
    #     book.title = title
    #     book.set_unique_metadata('DC', 'creator', author)
    #     #
    #     epub.write_epub(epub_ebook, book, {})
    #
    #     # .epub -> .mobi
    #     if ebook_format == 'epub':
    #         return
    #     else:
    #         print("convert format")
    #         try:
    #             os.system('ebook-convert "{}" "{}"'.format(epub_ebook, target_ebook))
    #         except Exception as e:
    #             print("convert ebook failed: {}".format(e))
    #         os.remove(epub_ebook)

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

    def download(self, book=None, author=None):
        """
        下载指定书籍或者指定作者的所有书
        :param book: 如果传入书名，则只下载该书
        :param author: 如果传入作者名，则下载该作者能搜索到的所有不重名书籍
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
        self.gen_recipes()
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

    def __init__(self):
        self.url = 'https://www.xbiquge6.com'
        self.name = '新笔趣阁'
        self.template = "novel_template1.recipe"

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

            return book, author, index_url, img_url

        #
        details_list = []
        for soup in books:
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
            'web_url': self.url
        }
        template = _ENV.get_template(self.template)
        cont = template.render(**details_dict)

        # save
        with open(recipe, 'w', encoding="utf-8") as file:
            file.write(cont)

        return recipe


class SubSpider2:

    def __init__(self):
        self.url = 'https://www.biquge.cc'
        self.name = '笔趣阁'
        self.template = "novel_template2.recipe"

    def search(self, book=None, author=None):
        """
        该网站的搜索是通过一个接口以参数siteid传入站点名进行请求，允许多个关键词，可以同时筛选书名和作者名；
        该网页的查询结果只会有一页
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
            'web_url': index_url
        }
        template = _ENV.get_template(self.template)
        cont = template.render(**details_dict)

        # save
        with open(recipe, 'w', encoding="utf-8") as file:
            file.write(cont)

        return recipe


if __name__ == "__main__":
    output = "novels"
    s = WebFictionSpider(output=output)
    s.download(book="诛仙")
    # s.download(author="云天空")
    s.download_books(["秘巫之主", "极品家丁"])


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
