from Products.CMFCore.utils import getToolByName
from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.sender.testing import PUBLISHER_SENDER_INTEGRATION_TESTING
from ftw.publisher.sender.workflows import interfaces
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from unittest2 import TestCase
from zope.component import getUtility


def activate_workflow_for_page(portal, workflow_id):
    wftool = getToolByName(portal, 'portal_workflow')
    wftool.setChainForPortalTypes(
        ['Document'], workflow_id)


EXAMPLE_WORKFLOW_PUBLISHED = 'publisher-example-workflow--STATUS--published'
EXAMPLE_WORKFLOW_REVISION = 'publisher-example-workflow--STATUS--revision'


class TestGetWorkflowConfig(TestCase):

    layer = PUBLISHER_SENDER_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

    def test_returns_config_for_example_workflow_page(self):
        activate_workflow_for_page(self.portal, 'publisher-example-workflow')
        page = create(Builder('page'))

        configs = getUtility(interfaces.IWorkflowConfigs)
        config = configs.get_config_for(page)
        self.assertTrue(config, 'There is no IWorkflowConfiguration')

    def test_returns_None_if_there_is_no_workflow(self):
        configs = getUtility(interfaces.IWorkflowConfigs)
        config = configs.get_config_for(self.portal)
        self.assertEquals(None, config)

    def test_returns_None_if_the_workflow_is_not_a_publisher_workflow(self):
        activate_workflow_for_page(self.portal, 'simple_publication_workflow')
        page = create(Builder('page'))

        configs = getUtility(interfaces.IWorkflowConfigs)
        config = configs.get_config_for(page)
        self.assertEquals(None, config)


class TestWorkflowConfigs(TestCase):

    layer = PUBLISHER_SENDER_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)
        activate_workflow_for_page(self.portal, 'publisher-example-workflow')

    def test_is_published(self):
        page_private = create(Builder('page'))
        page_published = create(Builder('page')
                                .in_state(EXAMPLE_WORKFLOW_PUBLISHED))
        configs = getUtility(interfaces.IWorkflowConfigs)

        self.assertFalse(configs.is_published(page_private))
        self.assertTrue(configs.is_published(page_published))

    def test_is_in_revision(self):
        page_private = create(Builder('page'))
        page_revision = create(Builder('page')
                               .in_state(EXAMPLE_WORKFLOW_REVISION))
        configs = getUtility(interfaces.IWorkflowConfigs)

        self.assertFalse(configs.is_in_revision(page_private))
        self.assertTrue(configs.is_in_revision(page_revision))
