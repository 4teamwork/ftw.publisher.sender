from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.sender.tests import FunctionalTestCase
from ftw.publisher.sender.tests.pages import Workflow
from ftw.testbrowser import browsing
from ftw.testbrowser.pages import statusmessages
from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName
import transaction


EXAMPLE_WF_ID = 'publisher-example-workflow'
EXAMPLE_WF_INTERNAL = 'publisher-example-workflow--STATUS--internal'
EXAMPLE_WF_PUBLISHED = 'publisher-example-workflow--STATUS--published'
EXAMPLE_WF_REVISION = 'publisher-example-workflow--STATUS--revision'


class TestExampleWFConstraintDefinition(FunctionalTestCase):


    def setUp(self):
        super(TestExampleWFConstraintDefinition, self).setUp()
        self.grant('Manager')

        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.setChainForPortalTypes(['Document', 'Folder', 'ContentPage'],
                                      EXAMPLE_WF_ID)

        transaction.commit()
        
    @browsing
    def test_warning_on_submit_when_parent_is_not_published(self, browser):
        folder = create(Builder('folder')
                        .in_state(EXAMPLE_WF_INTERNAL))
        page = create(Builder('page')
                      .within(folder)
                      .in_state(EXAMPLE_WF_INTERNAL))

        browser.login().visit(page)
        Workflow().do_transition('submit')

        statusmessages.assert_message('The parent object needs to be published first.')
        Workflow().assert_status('Pending')

    @browsing
    def test_error_on_publish_when_parent_is_not_published(self, browser):
        folder = create(Builder('folder')
                        .in_state(EXAMPLE_WF_INTERNAL))
        page = create(Builder('page')
                      .within(folder)
                      .in_state(EXAMPLE_WF_INTERNAL))

        browser.login().visit(page)
        Workflow().do_transition('publish', assert_success=False)

        statusmessages.assert_message('The parent object needs to be published first.')
        Workflow().assert_status('Internal')

    @browsing
    def test_no_error_when_parent_is_in_revision(self, browser):
        folder = create(Builder('folder')
                        .in_state(EXAMPLE_WF_REVISION))
        page = create(Builder('page')
                      .within(folder)
                      .in_state(EXAMPLE_WF_REVISION))

        browser.login().visit(page)
        Workflow().do_transition('publish')
        Workflow().assert_status('Published')

    @browsing
    def test_warning_on_retract_when_children_published(self, browser):
        folder = create(Builder('folder')
                        .in_state(EXAMPLE_WF_PUBLISHED))
        page = create(Builder('page')
                      .within(folder)
                      .in_state(EXAMPLE_WF_PUBLISHED))

        browser.login().visit(folder)
        Workflow().do_transition('retract')

        statusmessages.assert_message(
            'The child object <a href="http://nohost/plone'
            '/folder/document"></a> is still published.'
        )
        Workflow().assert_status('Internal')

        browser.visit(page)
        Workflow().assert_status('Published')

    @browsing
    def test_warning_when_child_is_in_revision(self, browser):
        folder = create(Builder('folder')
                        .in_state(EXAMPLE_WF_PUBLISHED))
        page = create(Builder('page')
                      .within(folder)
                      .in_state(EXAMPLE_WF_REVISION))

        browser.login().visit(folder)
        Workflow().do_transition('retract')

        statusmessages.assert_message(
            'The child object <a href="http://nohost/plone'
            '/folder/document"></a> is still published.'
        )
        Workflow().assert_status('Internal')

        browser.visit(page)
        Workflow().assert_status('Revision')

    @browsing
    def test_warning_on_publish_when_references_are_not_published(self, browser):
        page = create(Builder('page')
                      .titled('The Page'))
        other_page = create(Builder('page')
                            .titled('The Other Page'))
        page.setRelatedItems(other_page)
        transaction.commit()

        browser.login().visit(page)
        Workflow().do_transition('publish')
        statusmessages.assert_message(
            'The referenced object <a href="http://nohost/plone'
            '/the-other-page">The Other Page</a> is not yet published.'
        )


    @browsing
    def test_do_not_fail_if_reference_is_none(self, browser):
        page = create(Builder('page')
                      .titled('The Page'))
        other_page = create(Builder('page')
                            .titled('The Other Page'))
        page.setRelatedItems(other_page)

        self.portal._delObject(other_page.getId(), suppress_events=True)
        transaction.commit()

        browser.login().visit(page)
        Workflow().do_transition('publish')
        statusmessages.assert_no_error_messages()

    @browsing
    def test_warning_on_publish_when_sl_block_has_unpublished_references(self, browser):
        page=create(Builder('content page'))
        other_page=create(Builder('content page').titled('Other Page'))
        other_page_uuid=IUUID(other_page)
        create(Builder('text block')
               .having(text='<a href="resolveuid/%s">link</a>' % other_page_uuid)
               .within(page))

        browser.login().visit(page)
        Workflow().do_transition('publish')

        statusmessages.assert_message(
            'The referenced object <a href="http://nohost/plone'
            '/other-page">Other Page</a> is not yet published.'
        )

    @browsing
    def test_warning_on_retract_when_references_are_still_published(self, browser):
        page=create(Builder('page')
                      .titled('The Page')
                      .in_state(EXAMPLE_WF_PUBLISHED))
        other_page=create(Builder('page')
                            .titled('The Other Page')
                            .in_state(EXAMPLE_WF_PUBLISHED))
        page.setRelatedItems(other_page)
        transaction.commit()

        browser.login().visit(page)
        Workflow().do_transition('retract')

        statusmessages.assert_message(
            'The referenced object <a href="http://nohost/plone'
            '/the-other-page">The Other Page</a> is still published.'
        )

    @browsing
    def test_warning_on_retract_when_sl_block_has_published_references(self, browser):
        page=create(Builder('content page'))
        other_page=create(Builder('content page')
                            .titled('Other Page')
                            .in_state(EXAMPLE_WF_PUBLISHED))
        other_page_uuid=IUUID(other_page)
        create(Builder('text block')
               .having(text='<a href="resolveuid/%s">link</a>' % other_page_uuid)
               .within(page))

        browser.login().visit(page)
        # cannot add text block when published
        Workflow().do_transition('publish')
        Workflow().do_transition('retract')

        statusmessages.assert_message(
            'The referenced object <a href="http://nohost/plone'
            '/other-page">Other Page</a> is still published.'
        )
