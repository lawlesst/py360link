#import os
#import ez_setup
#ez_setup.use_setuptools()

from setuptools import setup, find_packages

setup(name='pylink360link',
    version='1',
    packages = find_packages('py360link'),
    package_dir = {'': 'py360link'},
    test_suite = 'py360link.test'
)
