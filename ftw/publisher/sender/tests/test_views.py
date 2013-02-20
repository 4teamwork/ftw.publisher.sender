from Products.PloneTestCase import ptc
from Products.statusmessages.interfaces import IStatusMessage
from ftw.publisher.sender.browser.views import PublishObject, DeleteObject
from ftw.publisher.sender.persistence import Queue
from ftw.publisher.sender.tests.layer import Layer
import transaction
import unittest


class TestPublishObject(ptc.PloneTestCase):
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
        self.assertEquals(isinstance(PublishObject(self.portal,self.portal.REQUEST), PublishObject), True)


class TestDeleteObject(ptc.FunctionalTestCase):

    layer = Layer

    def afterSetUp(self):
        # add some default plone types
        testdoc2id = self.folder.invokeFactory('Document', 'test-doc-2')
        self.testdoc2 = getattr(self.folder,testdoc2id,None)

    def get_status_messages(self):
        return map(lambda msg: str(msg.message),
                   IStatusMessage(self.testdoc2.REQUEST).show())

    def test_delete_object(self):
        queue = Queue(self.testdoc2)
        self.assertEquals(queue.countJobs(),0)
        DeleteObject(self.testdoc2,self.testdoc2.REQUEST)()
        self.assertEquals(queue.countJobs(),1)
        self.assertEquals(queue.getJobs()[0].action,'delete')

        transaction.commit()
        self.assertEquals(
            self.get_status_messages(),
            ['This object will be deleted at the remote sites.'])

    def test_delete_plonesiteroot(self):
        self.assertRaises(Exception, DeleteObject(
                self.portal,self.portal.REQUEST))

    def test_delete_with_rollback(self):
        # This test simulates Products.CMFPlone.utils.isLinked which
        # deletes and rolls back for integrity checking.
        # When it is rolled back it should create a status message.
        queue = Queue(self.testdoc2)
        self.assertEquals(queue.countJobs(), 0)

        savepoint = transaction.savepoint()
        DeleteObject(self.testdoc2, self.testdoc2.REQUEST)()
        self.assertEquals(queue.countJobs(), 1)

        savepoint.rollback()
        self.assertEquals(queue.countJobs(), 0)

        transaction.commit()
        self.assertEquals(self.get_status_messages(), [])




# XXX disabled for now, since installation of PloneFormGen seems
# not to work properly.
# class TestFormGenIntegration(PloneTestCase):
#     layer = Layer

#     def afterSetUp(self):
#         self.loginAsPortalOwner()
#         # import pdb; pdb.set_trace( )
#         self.folder.invokeFactory('FormFolder', 'ff1')
#         self.ff1 = getattr(self.folder, 'ff1')



#     def test_publish_form(self):

#         self.assertEquals(1, 0)



def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
