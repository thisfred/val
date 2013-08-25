import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand

import val


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='val',
    version=val.__version__,
    author='Eric Casteleijn',
    author_email='thisfred@gmail.com',
    description='Python object validator',
    license='BSD',
    keywords='validation validators',
    url='http://github.com/thisfred/val',
    long_description=open('README.md').read(),
    packages=['val'],
    cmdclass={'test': PyTest},
    tests_require=['pytest', 'Pyth'],
    test_suite='tests')
