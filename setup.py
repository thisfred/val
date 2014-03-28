"""
val: A validator for arbitrary python objects.

Copyright (c) 2013-2014
Eric Casteleijn, <thisfred@gmail.com>
"""
from setuptools import setup

import val

setup(
    name='val',
    version=val.__version__,
    author='Eric Casteleijn',
    author_email='thisfred@gmail.com',
    description='Python object validator',
    license='BSD',
    keywords='validation validators',
    url='http://github.com/thisfred/val',
    py_modules=['val'],
    long_description=open('README.rst').read(),
    tests_require=[
        'flatland', 'schema', 'nose', 'nose-cov', 'flake8', 'pylint'],
    test_suite='test_val')
