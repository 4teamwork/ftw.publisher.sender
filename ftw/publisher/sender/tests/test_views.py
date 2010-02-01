import unittest

from Products.PloneTestCase.ptc import PloneTestCase
from ftw.publisher.sender.tests.layer import Layer

from ftw.publisher.sender.browser.views import PublishObject, DeleteObject
from ftw.publisher.sender.persistence import Queue

class TestPublishObject(PloneTestCase):
    layer = Layer
    
    def afterSetUp(self):
        # add some default plone types
        testdoc2id = self.folder.invokeFactory('Document', 'test-doc-2')
        self.testdoc2 = getattr(self.folder,testdoc2id,None)

    def test_publish_object(self):
        queue = Queue(self.testdoc2)
        self.assertEquals(queue.countJobs(),0)
        PublishObject(self.testdoc2,self.testdoc2.REQUEST)()
        self.assertEquals(queue.countJobs(),1)
        self.assertEquals(queue.getJobs()[0].action,'push')
        
    def test_publish_plonesiteroot(self):
        self.assertRaises(Exception, PublishObject(self.portal,self.portal.REQUEST))


class TestDeleteObject(PloneTestCase):
    layer = Layer

    def afterSetUp(self):
        # add some default plone types
        testdoc2id = self.folder.invokeFactory('Document', 'test-doc-2')
        self.testdoc2 = getattr(self.folder,testdoc2id,None)

    def test_delete_object(self):
        queue = Queue(self.testdoc2)
        self.assertEquals(queue.countJobs(),0)
        DeleteObject(self.testdoc2,self.testdoc2.REQUEST)()
        self.assertEquals(queue.countJobs(),1)
        self.assertEquals(queue.getJobs()[0].action,'delete')

    def test_delete_plonesiteroot(self):
        self.assertRaises(Exception, DeleteObject(self.portal,self.portal.REQUEST))

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)