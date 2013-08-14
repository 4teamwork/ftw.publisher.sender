from Products.CMFCore.utils import getToolByName
from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.sender.testing import PUBLISHER_SENDER_INTEGRATION_TESTING
from ftw.publisher.sender.workflows.interfaces import IModifyStatus
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from unittest2 import TestCase
from zope.interface.verify import verifyObject


EXAMPLE_WF_ID = 'publisher-example-workflow'
EXAMPLE_WF_PUBLISH = '%s--TRANSITION--publish--internal_published' % (
    EXAMPLE_WF_ID)
EXAMPLE_WF_RETRACT = '%s--TRANSITION--retract--published_internal' % (
    EXAMPLE_WF_ID)
EXAMPLE_WF_PUBLISHED = 'publisher-example-workflow--STATUS--published'


class TestModifyStatusView(TestCase):

    layer = PUBLISHER_SENDER_INTEGRATION_TESTING

    def setUp(self):
        super(TestModifyStatusView, self).setUp()

        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

        self.wftool = getToolByName(self.portal, 'portal_workflow')
        self.wftool.setChainForPortalTypes(['Document', 'Folder'],
                                           'publisher-example-workflow')

    def test_browser_view_is_registered(self):
        view = self.portal.unrestrictedTraverse('publisher-modify-status',
                                                default=None)
        self.assertTrue(view)

    def test_browser_view_implements_interface(self):
        view = self.portal.unrestrictedTraverse('publisher-modify-status')

        self.assertTrue(IModifyStatus.providedBy(view))
        verifyObject(IModifyStatus, view)

    def test_get_transition_action(self):
        page = create(Builder('page'))
        view = page.unrestrictedTraverse('publisher-modify-status')

        self.assertEqual(
            view.get_transition_action(EXAMPLE_WF_PUBLISH),
            '%s/content_status_modify?workflow_action=%s' % (
                page.absolute_url(), EXAMPLE_WF_PUBLISH))

    def test_is_transaction_allowed(self):
        folder = create(Builder('folder').in_state(EXAMPLE_WF_PUBLISHED))
        page = create(Builder('page').within(folder))
        view = page.unrestrictedTraverse('publisher-modify-status')
        self.assertTrue(view.is_transition_allowed(EXAMPLE_WF_PUBLISH))
