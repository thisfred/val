"""
val: A validator for arbitrary python objects.

Copyright (c) 2013-2014
Eric Casteleijn, <thisfred@gmail.com>
"""
from setuptools import setup

import codecs
import os
import re


HERE = os.path.abspath(os.path.dirname(__file__))


def find_version(*file_paths):
    # Open in Latin-1 so that we avoid encoding errors.
    # Use codecs.open for Python 2 compatibility
    with codecs.open(os.path.join(HERE, *file_paths), 'r', 'latin1') as f:
        version_file = f.read()

    # The version line must have the form
    # __version__ = 'ver'
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
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
    long_description=open('README.rst').read(),
    tests_require=['nose', 'nose-cov', 'flake8', 'pylint'],
    test_suite='test_val')
