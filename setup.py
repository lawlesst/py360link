#import os
#import ez_setup
#ez_setup.use_setuptools()

from setuptools import setup, find_packages

setup(name='pylink360',
    version='1',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    test_suite = 'py360link.test'
)
