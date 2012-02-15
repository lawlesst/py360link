#import os
#import ez_setup
#ez_setup.use_setuptools()

from setuptools import setup, find_packages

setup(name='pylink360',
    version='0.1',
    packages=find_packages(),
    #package_dir = {'': 'py360link'},
    #package_data={'pylink360': ['test_data/*.*']},
    test_suite = 'py360link.test'
)
