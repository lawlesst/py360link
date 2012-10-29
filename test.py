import unittest
from test import link360

def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(link360.suite())
    return test_suite

runner = unittest.TextTestRunner()
results = runner.run(suite())

if results.wasSuccessful():
    pass
else:
    raise Exception('Unit tests did not pass.  Check output.')
