RunSpiders
^^^^^^^^^^^

|Python3|

A python library contains many predefined powerful web crawlers.

**Attention**: this package probably can't work properly because of the correlated webs' updates.
If this situation happens, just fix it on your own.

Installation
>>>>>>>>>>>>>

.. code:: bash

    pip install RunSpiders

Requirements
>>>>>>>>>>>>>

.. code:: python

    from RunSpiders import Checker

    checker = Checker()
    checker.main()

1. [calibre](https://calibre-ebook.com/download) for converting ebook
[Mac安装Calibre电子书应用](https://blog.csdn.net/u012955829/article/details/99240602)

.. code::bash

    vim ~/.bash_profile
    export EBOOK_PATH=/Applications/calibre.app/Contents/MacOS
    export PATH=$PATH:$EBOOK_PATH

2. [MAC 系统安装FFmpeg](https://www.jianshu.com/p/73441acf7815)

Examples
>>>>>>>>>>>>>

novel
::::::::::::::::
Please install calibre and add `ebook-convert` to environment variables.

.. code:: python

    from RunSpiders import WebFictionSpider

    output = "F:/ebooks"
    spider = WebFictionSpider(output)

    s.download(book="诛仙")
    s.download(author="云天空")
    s.download_books(["秘巫之主", "极品家丁"])

movie
::::::::::::::::
Please install ffmpeg and add it to environment variables.

.. code:: python

    from RunSpiders.video.base.m3u8 import M3U8Spider

    spider = M3U8Spider(output="F\movies")
    spider.download_movies([(m3u8_url, file_name), ...])


.. |Python3| image:: https://img.shields.io/badge/python-3-red.svg


FAQ
>>>>>>>>>>>>>
IPython报错
::::::::::::::::
- 问题：ImportError: cannot import name 'generator_to_async_generator'
- 解决方案：``pip install ipython prompt_toolkit --upgrade``
