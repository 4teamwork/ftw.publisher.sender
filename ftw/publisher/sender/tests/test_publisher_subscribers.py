from Products.CMFCore.utils import getToolByName
from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.sender.interfaces import IQueue
from ftw.publisher.sender.testing import PUBLISHER_SENDER_FUNCTIONAL_TESTING
from ftw.publisher.sender.tests.pages import Workflow
from ftw.testing.pages import Plone
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from unittest2 import TestCase
import transaction


EXAMPLE_WF_ID = 'publisher-example-workflow'
EXAMPLE_WF_PUBLISHED = '%s--STATUS--published' % EXAMPLE_WF_ID


class TestPublisherTransitionEventHandler(TestCase):

    layer = PUBLISHER_SENDER_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.setChainForPortalTypes(['Document'], EXAMPLE_WF_ID)
        transaction.commit()

    def test_push_job_in_publisher_queue_after_publishing(self):
        page = create(Builder('page'))
        Plone().login().visit(page)
        Workflow().do_transition('publish')

        queue = IQueue(self.portal)
        self.assertEquals(1, queue.countJobs())

        job = queue.getJobs()[0]
        self.assertEquals('push', job.action)
        self.assertEquals(page, job.getObject(self.portal))

    def test_no_job_on_submit(self):
        page = create(Builder('page'))
        Plone().login().visit(page)
        Workflow().do_transition('submit')

        queue = IQueue(self.portal)
        self.assertEquals(0, queue.countJobs())

    def test_no_job_on_revise(self):
        page = create(Builder('page').in_state(EXAMPLE_WF_PUBLISHED))
        Plone().login().visit(page)
        Workflow().do_transition('revise')

        queue = IQueue(self.portal)
        self.assertEquals(0, queue.countJobs())
