#! /usr/bin/env python

import codecs
from setuptools import setup

with codecs.open("README.md", encoding="utf-8") as f:
    readme = f.read()

setup(
    name="aerate",
    version="0.0.1",
    description="A Doxygen to Sphinx bridge",
    long_description=readme,
    author="Kaiting Chen",
    author_email="ktchen14@gmail.com",
    url="https://github.com/ktchen14/aerate",
    packages=["aerate"],
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Documentation",
        "Topic :: Software Development :: Documentation",
    ],
)
