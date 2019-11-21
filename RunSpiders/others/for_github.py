# -*- coding: utf-8 -*-
# @Time     : 2019/10/23 14:55
# @Author   : Run 
# @File     : for_github.py
# @Software : PyCharm


from RunSpiders.templates import _ENV
from RunSpiders.utils import *
import re
from bs4 import BeautifulSoup
from IPython.display import HTML


def get_popularity_info(project_github_url):
    """
    Notes: todo
        1. 不是所有项目都会显示'Used by'信息，并且登录后才能查看该信息，故暂不做爬取。
        2. 如何设置href导向的链接在新标签页中打开。
        3. 美化introduction部分
    :param project_github_url:
    :return:
    """
    tmp = re.split(r'[\/\\]+', project_github_url)
    author, package = tmp[-2:]
    flag, req = request_url(project_github_url)
    if not flag:
        print("crawl project's github homepage failed: {}".format(project_github_url))
        return ''
    cont = req.text
    soup = BeautifulSoup(cont, 'lxml')
    #
    try:
        introduction = str(soup.find('div', attrs={'class', 'f4'}))
        watch = re.search('(\d+) users* (are|is) watching this repository', cont).groups()[0]
        star = re.search('(\d+) users starred this repository', cont).groups()[0]
        fork = re.search('(\d+) users forked this repository', cont).groups()[0]
    except:
        print("can't get target labels")
        return ''
    # fill template
    details_dict = {
        'author': author,
        'href': project_github_url,
        'package': package,
        'watch': watch,
        'star': star,
        'fork': fork,
        'introduction': introduction
    }
    template = _ENV.get_template('github_popularity_template1.html')
    cont = template.render(**details_dict)

    return HTML(cont)

