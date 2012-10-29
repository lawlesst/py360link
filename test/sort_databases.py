"""
Test the database sort method.
"""

import os
try:
    import json
except ImportError:
    import simplejson as json
import unittest
from pprint import pprint

from py360link import sort_databases

#Directory where test data is stored.  
DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),'data')

def read_data(filename):
    path = os.path.join(DATA_PATH, filename)
    content = open(path)
    return content



class TestSortDBs(unittest.TestCase):
    def setUp(self):
        self.links = [
        {'anchor': 'EBSCOhost',
          'coverage_start': '1991-01-05',
          'provider': 'EBSCOhost',
          'type': 'source',
          'url': 'http://search.ebscohost.com/direct.asp?db=aph'},
         {'anchor': 'LexisNexis',
          'coverage_start': '1995-01-01',
          'provider': 'LexisNexis',
          'type': 'source',
          'url': 'https://www.lexisnexis.com/hottopics/lnacademic/?'
          },
          {'anchor': 'Elsevier',
          'coverage_start': '1995-01-07',
          'provider': 'Elsevier',
          'type': 'source',
          'url': 'http://www.sciencedirect.com'
          },
          ]


    def test_push_top(self):
        sort_databases.PUSH_TOP = ['LexisNexis']
        sort_databases.PUSH_BOTTOM = ['Elsevier']
        new = sort_databases.do_sort(self.links)
        self.assertEqual(new[0]['provider'], 'LexisNexis')
        sort_databases.PUSH_TOP = ['EBSCOhost']
        new = sort_databases.do_sort(self.links)
        self.assertEqual(new[0]['provider'], 'EBSCOhost')

    def test_push_bottom(self):
        sort_databases.PUSH_BOTTOM = ['LexisNexis']
        new = sort_databases.do_sort(self.links)
        self.assertEqual(new[-1]['provider'], 'LexisNexis')

    def test_sort_by(self):
        sort_databases.SORT_BY = ['Elsevier', 'EBSCOhost', 'LexisNexis']
        new = sort_databases.do_sort(self.links)
        #top
        self.assertEqual(new[0]['provider'], 'Elsevier')
        #middle
        self.assertEqual(new[1]['provider'], 'EBSCOhost')
        #last
        self.assertEqual(new[-1]['provider'], 'LexisNexis')

    def test_no_order(self):
        sort_databases.PUSH_TOP = []
        sort_databases.PUSH_BOTTOM = []
        sort_databases.SORT_BY = []
        new = sort_databases.do_sort(self.links)
        #top
        self.assertEqual(new[0]['provider'], 'EBSCOhost')
        #middle
        self.assertEqual(new[1]['provider'], 'LexisNexis')
        #bottom
        self.assertEqual(new[-1]['provider'], 'Elsevier')



def suite():
    suite1 = unittest.makeSuite(TestSortDBs, 'test')
    all_tests = unittest.TestSuite((suite1,))
    return all_tests

if __name__ == '__main__':
    unittest.main()