"""
val: A validator for arbitrary python objects.

Copyright (c) 2013-2014
Eric Casteleijn, <thisfred@gmail.com>
"""
from setuptools import setup

import os
import re


HERE = os.path.abspath(os.path.dirname(__file__))


def find_version(file_path):
    """Get version from designated file."""
    with open(os.path.join(HERE, file_path), 'r') as version_file:
        contents = version_file.read()
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", contents, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name='val',
    version=find_version('val.py'),
    author='Eric Casteleijn',
    author_email='thisfred@gmail.com',
    description='Python object validator',
    license='BSD',
    keywords='validation validators',
    url='http://github.com/thisfred/val',
    py_modules=['val'],
    long_description=open('README.rst').read())
