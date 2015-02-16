"""
val: A validator for arbitrary python objects.

Copyright (c) 2013-2014
Eric Casteleijn, <thisfred@gmail.com>
"""
from setuptools import setup

import os
import re


def find_version(*file_paths):
    """Get version from python file."""
    with open(os.path.join(os.path.dirname(__file__),
                           *file_paths)) as version_file:
        contents = version_file.read()
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", contents, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


HERE = os.path.abspath(os.path.dirname(__file__))

setup(
    name='val',
    version=find_version('val/__init__.py'),
    author='Eric Casteleijn',
    author_email='thisfred@gmail.com',
    description='Python object validator',
    license='BSD',
    keywords='validation validators',
    url='http://github.com/thisfred/val',
    packages=['val'],
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4'])
