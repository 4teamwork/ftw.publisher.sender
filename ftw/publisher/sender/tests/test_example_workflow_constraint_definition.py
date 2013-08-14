from Products.CMFCore.utils import getToolByName
from ftw.builder import Builder
from ftw.builder import create
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
EXAMPLE_WF_INTERNAL = 'publisher-example-workflow--STATUS--internal'
EXAMPLE_WF_PUBLISHED = 'publisher-example-workflow--STATUS--published'
EXAMPLE_WF_REVISION = 'publisher-example-workflow--STATUS--revision'


class TestExampleWFConstraintDefinition(TestCase):

    layer = PUBLISHER_SENDER_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        setRoles(self.portal, TEST_USER_ID, ['Manager', 'Reviewer'])
        login(self.portal, TEST_USER_NAME)

        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.setChainForPortalTypes(['Document', 'Folder'], EXAMPLE_WF_ID)

        transaction.commit()

    def test_warning_on_submit_when_parent_is_not_published(self):
        folder = create(Builder('folder')
                        .in_state(EXAMPLE_WF_INTERNAL))
        page = create(Builder('page')
                      .within(folder)
                      .in_state(EXAMPLE_WF_INTERNAL))

        Plone().login().visit(page)
        Workflow().do_transition('submit')

        Workflow().assert_portal_message(
            'warning', 'The parent object needs to be published first.')
        Workflow().assert_status('Pending')

    def test_error_on_submit_when_parent_is_not_published(self):
        folder = create(Builder('folder')
                        .in_state(EXAMPLE_WF_INTERNAL))
        page = create(Builder('page')
                      .within(folder)
                      .in_state(EXAMPLE_WF_INTERNAL))

        Plone().login().visit(page)
        Workflow().do_transition('publish', assert_success=False)

        Workflow().assert_portal_message(
            'error', 'The parent object needs to be published first.')
        Workflow().assert_status('Internal')

    def test_warning_on_retract_when_children_published(self):
        folder = create(Builder('folder')
                        .in_state(EXAMPLE_WF_PUBLISHED))
        page = create(Builder('page')
                      .within(folder)
                      .in_state(EXAMPLE_WF_PUBLISHED))

        Plone().login().visit(folder)
        Workflow().do_transition('retract')

        Workflow().assert_portal_message(
            'warning', 'The child object <a href="http://nohost/plone'
            '/folder/document"></a> is still published.')
        Workflow().assert_status('Internal')

        Workflow().visit(page).assert_status('Published')

    def test_warning_on_publish_when_references_are_not_published(self):
        page = create(Builder('page')
                      .titled('The Page'))
        other_page = create(Builder('page')
                            .titled('The Other Page'))
        page.setRelatedItems(other_page)
        transaction.commit()

        Plone().login().visit(page)
        Workflow().do_transition('publish')

        Workflow().assert_portal_message(
            'warning', 'The referenced object <a href="http://nohost/plone'
            '/the-other-page">The Other Page</a> is not yet published.')

    def test_warning_on_retract_when_references_are_still_published(self):
        page = create(Builder('page')
                      .titled('The Page')
                      .in_state(EXAMPLE_WF_PUBLISHED))
        other_page = create(Builder('page')
                            .titled('The Other Page')
                            .in_state(EXAMPLE_WF_PUBLISHED))
        page.setRelatedItems(other_page)
        transaction.commit()

        Plone().login().visit(page)
        Workflow().do_transition('retract')

        Workflow().assert_portal_message(
            'warning', 'The referenced object <a href="http://nohost/plone'
            '/the-other-page">The Other Page</a> is still published.')