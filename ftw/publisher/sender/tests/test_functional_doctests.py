import unittest
import doctest

from Testing import ZopeTestCase
from Products.PloneTestCase import ptc
from ftw.publisher.sender.tests import flayer

MODULENAMES = [
]

TESTFILES = [
    'blacklist.txt',
    'storage.txt',
    'utils.txt',
]

OPTIONFLAGS = (doctest.NORMALIZE_WHITESPACE|
               doctest.ELLIPSIS|
               doctest.REPORT_NDIFF)


def test_suite():

    suite = unittest.TestSuite()

    for testfile in TESTFILES:
        fdfs = ZopeTestCase.FunctionalDocFileSuite(
            testfile,
            optionflags=OPTIONFLAGS,
            test_class=ptc.FunctionalTestCase,)
        fdfs.layer = flayer.layer
        suite.addTest(fdfs)

    for module in MODULENAMES:
        fdts = ZopeTestCase.FunctionalDocTestSuite(
            module,
            optionflags=OPTIONFLAGS,
            test_class=ptc.FunctionalTestCase)
        fdts.layer = flayer.layer
        suite.addTest(fdts)

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
