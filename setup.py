#! /usr/bin/env python

import os
from setuptools import setup

root = os.path.abspath(path.dirname(__file__))
with open(os.path.join(root, "README.md"), encoding="utf-8") as f:
    readme = f.read()

setup(
    name="Aerate",
    version="0.0.1",
    description="A Doxygen to Sphinx bridge",
    long_description=readme,
    long_description_content_type="text/markdown",
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
    python_requires='>=3.6',
)
