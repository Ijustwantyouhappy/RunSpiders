# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import re


setup(
    name="RunSpiders",
    version=re.findall('__version__\s*=\s*"(.*?)"', open("RunSpiders/__init__.py", "r", encoding="utf-8").read())[0],
    author='Ijustwantyouhappy',
    author_email='',
    description="Some predefined web crawlers",
    long_description=open('README.rst').read(),  # todo write README seriously
    # long_description_content_type="text/markdown",
    url='',
    # maintainer='',
    # maintainer_email='',
    license='MIT',  # todo write LICENSE seriously
    packages=find_packages(),
    # package_data = {
    #     '': ['*.recipe', '*.html']
    # },
    include_package_data=True,
    zip_safe=False,
    # platforms=["all"],
    python_requires='>=3.5',
    install_requires=["requests>=2.14.2",
                      "beautifulsoup4>=4.5.1",
                      "jinja2>=2.10.1",
                      "pycryptodome>=3.8.2",
                      "gevent>=1.1.2",
                      "tqdm>=4.32.2",
                      'selenium',
                      'js2py',
                      'prettytable'],
    classifiers=[
        "Environment :: Web Environment",
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Windows',
        "Topic :: Software Development :: Libraries :: Python Modules",
        'Programming Language :: Python :: 3'
    ],
    keywords='spiders'
)
