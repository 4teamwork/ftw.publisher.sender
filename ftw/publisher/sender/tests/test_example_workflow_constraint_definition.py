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
from plone.uuid.interfaces import IUUID
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
        wftool.setChainForPortalTypes(['Document', 'Folder', 'ContentPage'],
                                      EXAMPLE_WF_ID)

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

    def test_error_on_publish_when_parent_is_not_published(self):
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

    def test_no_error_when_parent_is_in_revision(self):
        folder = create(Builder('folder')
                        .in_state(EXAMPLE_WF_REVISION))
        page = create(Builder('page')
                      .within(folder)
                      .in_state(EXAMPLE_WF_REVISION))

        Plone().login().visit(page)
        Workflow().do_transition('publish')
        Workflow().assert_status('Published')

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

    def test_warning_when_child_is_in_revision(self):
        folder = create(Builder('folder')
                        .in_state(EXAMPLE_WF_PUBLISHED))
        page = create(Builder('page')
                      .within(folder)
                      .in_state(EXAMPLE_WF_REVISION))

        Plone().login().visit(folder)
        Workflow().do_transition('retract')

        Workflow().assert_portal_message(
            'warning', 'The child object <a href="http://nohost/plone'
            '/folder/document"></a> is still published.')
        Workflow().assert_status('Internal')

        Workflow().visit(page).assert_status('Revision')

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

    def test_do_not_fail_if_reference_is_none(self):
        page = create(Builder('page')
                      .titled('The Page'))
        other_page = create(Builder('page')
                            .titled('The Other Page'))
        page.setRelatedItems(other_page)

        self.portal._delObject(other_page.getId(), suppress_events=True)
        transaction.commit()

        Plone().login().visit(page)
        Workflow().do_transition('publish')
        self.assertFalse(len(Workflow().portal_messages()['warning']),
                         'No waring expected, since the ref does not exists '
                         'anymore.')

    def test_warning_on_publish_when_sl_block_has_unpublished_references(self):
        page=create(Builder('content page'))
        other_page=create(Builder('content page').titled('Other Page'))
        other_page_uuid=IUUID(other_page)
        create(Builder('text block')
               .having(text='<a href="resolveuid/%s">link</a>' % other_page_uuid)
               .within(page))

        Plone().login().visit(page)
        Workflow().do_transition('publish')

        Workflow().assert_portal_message(
            'warning', 'The referenced object <a href="http://nohost/plone'
            '/other-page">Other Page</a> is not yet published.')

    def test_warning_on_retract_when_references_are_still_published(self):
        page=create(Builder('page')
                      .titled('The Page')
                      .in_state(EXAMPLE_WF_PUBLISHED))
        other_page=create(Builder('page')
                            .titled('The Other Page')
                            .in_state(EXAMPLE_WF_PUBLISHED))
        page.setRelatedItems(other_page)
        transaction.commit()

        Plone().login().visit(page)
        Workflow().do_transition('retract')

        Workflow().assert_portal_message(
            'warning', 'The referenced object <a href="http://nohost/plone'
            '/the-other-page">The Other Page</a> is still published.')

    def test_warning_on_retract_when_sl_block_has_published_references(self):
        page=create(Builder('content page'))
        other_page=create(Builder('content page')
                            .titled('Other Page')
                            .in_state(EXAMPLE_WF_PUBLISHED))
        other_page_uuid=IUUID(other_page)
        create(Builder('text block')
               .having(text='<a href="resolveuid/%s">link</a>' % other_page_uuid)
               .within(page))

        Plone().login().visit(page)
        # cannot add text block when published
        Workflow().do_transition('publish')
        Workflow().do_transition('retract')

        Workflow().assert_portal_message(
            'warning', 'The referenced object <a href="http://nohost/plone'
            '/other-page">Other Page</a> is still published.')
