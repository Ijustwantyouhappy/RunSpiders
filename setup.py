# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import re


setup(
    name="RunSpiders",
    version=re.findall('__version__\s*=\s*"(.*?)"', open("RunSpiders/__init__.py", "r", encoding="utf-8").read())[0],
    author='Ijustwantyouhappy',
    author_email='',
    description="A python library contains many powerful web crawlers.",
    long_description=open('README.rst').read(),  # todo write README seriously
    # long_description_content_type="text/markdown",
    url='',
    # maintainer='',
    # maintainer_email='',
    license='MIT',
    packages=find_packages(),
    # package_data = {
    #     '': ['*.recipe', '*.html']
    # },
    include_package_data=True,
    zip_safe=False,
    # platforms=["all"],
    python_requires='>=3.5',
    install_requires=["requests",
                      "beautifulsoup4",
                      "jinja2",
                      "pycryptodome",
                      "gevent",
                      "tqdm",
                      'selenium',
                      'js2py',
                      'prettytable'],
    classifiers=[
        "Environment :: Web Environment",
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Windows',
        'Operating System :: MacOS',
        "Topic :: Software Development :: Libraries :: Python Modules",
        'Programming Language :: Python :: 3'
    ],
    keywords='spiders'
)
