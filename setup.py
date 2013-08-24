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
    long_description=open('README.md').read(),
    tests_require=[
        'flatland', 'schema', 'nose', 'coverage', 'flake8', 'pylint'],
    test_suite='tests')
