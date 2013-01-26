#import os
#import ez_setup
#ez_setup.use_setuptools()

from setuptools import setup, find_packages

setup(name='py360link',
    version='1.1',
    packages = find_packages(),
    test_suite = 'py360link.test'
)
