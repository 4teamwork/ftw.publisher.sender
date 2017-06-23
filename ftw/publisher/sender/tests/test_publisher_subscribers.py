from Products.CMFCore.utils import getToolByName
from ftw.builder import Builder
from ftw.builder import create
from ftw.testbrowser import browsing
from ftw.publisher.sender.interfaces import IQueue
from ftw.publisher.sender.tests import FunctionalTestCase
from ftw.publisher.sender.tests.pages import Workflow
import transaction


EXAMPLE_WF_ID = 'publisher-example-workflow'
EXAMPLE_WF_PUBLISHED = '%s--STATUS--published' % EXAMPLE_WF_ID


class TestPublisherTransitionEventHandler(FunctionalTestCase):

    def setUp(self):
        super(TestPublisherTransitionEventHandler, self).setUp()
        self.grant('Manager')

        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.setChainForPortalTypes(['Document'], EXAMPLE_WF_ID)
        transaction.commit()

    @browsing
    def test_push_job_in_publisher_queue_after_publishing(self, browser):
        page = create(Builder('page'))
        browser.login().visit(page)
        Workflow().do_transition('publish')

        queue = IQueue(self.portal)
        self.assertEquals(1, queue.countJobs())

        job = queue.getJobs()[0]
        self.assertEquals('push', job.action)
        self.assertEquals(page, job.getObject(self.portal))

    @browsing
    def test_no_job_on_submit(self, browser):
        page = create(Builder('page'))
        browser.login().visit(page)
        Workflow().do_transition('submit')

        queue = IQueue(self.portal)
        self.assertEquals(0, queue.countJobs())

    @browsing
    def test_no_job_on_revise(self, browser):
        page = create(Builder('page').in_state(EXAMPLE_WF_PUBLISHED))
        browser.login().visit(page)
        Workflow().do_transition('revise')

        queue = IQueue(self.portal)
        self.assertEquals(0, queue.countJobs())



class TestDeleteEventHandler(FunctionalTestCase):

    def setUp(self):
        super(TestDeleteEventHandler, self).setUp()
        self.grant('Manager')

        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.setChainForPortalTypes(['Folder'], EXAMPLE_WF_ID)
        transaction.commit()

    @browsing
    def test_no_job_when_object_has_no_publisher_workflow(self, browser):
        queue = IQueue(self.portal)
        page = create(Builder('page'))
        browser.login().visit(page, view='delete_confirmation')
        self.assertEquals(0, queue.countJobs())
        browser.click_on('Delete')
        self.assertEquals(0, queue.countJobs())

    @browsing
    def test_delete_job_create_when_we_have_a_publisher_workflow(self, browser):
        queue = IQueue(self.portal)
        folder = create(Builder('folder'))
        browser.login().visit(folder, view='delete_confirmation')
        self.assertEquals(0, queue.countJobs())
        browser.click_on('Delete')
        self.assertEquals(1, queue.countJobs())

        job = queue.getJobs()[0]
        self.assertEquals('delete', job.action)
        self.assertEquals('/plone/folder', job.objectPath)

    @browsing
    def test_delete_job_create_when_parent_has_publisher_workflow(self, browser):
        queue = IQueue(self.portal)
        folder = create(Builder('folder'))
        page = create(Builder('page').within(folder))

        browser.login().visit(page, view='delete_confirmation')
        self.assertEquals(0, queue.countJobs())
        browser.click_on('Delete')
        self.assertEquals(1, queue.countJobs())

        job = queue.getJobs()[0]
        self.assertEquals('delete', job.action)
        self.assertEquals('/plone/folder/document', job.objectPath)
