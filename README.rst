RunSpiders
^^^^^^^^^^^

|Python3|

A python library contains some predefined web crawlers.
Attention: this package probably can't work properly because of the correlated webs updates.
If this situation happens, just fix it on your own.

Installation
>>>>>>>>>>>>>

.. code:: bash

    pip install RunSpiders

Examples
>>>>>>>>>>>>>

novel
::::::::::::::::
Please install calibre and add `ebook-convert` to environment variables.

.. code:: python

    from RunSpiders import NovelSpider

    spider = NovelSpider()
    spider.download_books(['***', ...])
    # spider.download_books(['***', ...], style="recipe_first")

movie
::::::::::::::::
Please install ffmpeg and add it to environment variables.

.. code:: python

    from RunSpiders import M3U8Spider

    spider = M3U8Spider(output="F\movies")
    spider.download_movies([(m3u8_url, file_name), ...])


.. |Python3| image:: https://img.shields.io/badge/python-3-red.svg