# -*- coding: utf-8 -*-
import os
try:
    import json
except ImportError:
    import simplejson as json
import unittest
from pprint import pprint

#Directory where test data is stored.  
DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),'data')

def read_data(filename):
    path = os.path.join(DATA_PATH, filename)
    content = open(path).read()
    return content

class TestParseResponse(unittest.TestCase):

    def test_article(self):
        content = read_data('article.xml')
        print content

def suite():
    suite1 = unittest.makeSuite(TestParseResponse, 'test')
    all_tests = unittest.TestSuite((suite1,))
    return all_tests

if __name__ == '__main__':
    unittest.main()
