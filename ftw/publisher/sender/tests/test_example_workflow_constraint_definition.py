from ftw.builder import Builder
from ftw.builder import create
from plone import api
from plone.app.textfield.value import RichTextValue
from ftw.publisher.sender.tests import helpers
from ftw.publisher.sender.tests import FunctionalTestCase
from ftw.publisher.sender.tests.pages import Workflow
from ftw.testbrowser import browsing
from ftw.testbrowser.pages import statusmessages
from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
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
        wftool.setChainForPortalTypes(['Document', 'Folder', 'ftw.simplelayout.ContentPage'],
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
                      .titled(u'The Page'))
        other_page = create(Builder('page')
                            .titled(u'The Other Page'))
        helpers.set_related_items(page, other_page)

        browser.login().visit(page)
        Workflow().do_transition('publish')
        statusmessages.assert_message(
            'The referenced object <a href="http://nohost/plone'
            '/the-other-page">The Other Page</a> is not yet published.'
        )

    @browsing
    def test_warning_shown_when_referencing_children_with_separate_workflow(self, browser):
        parent = create(Builder('folder').titled(u'Parent'))
        child = create(Builder('folder').titled(u'Child').within(parent))
        helpers.set_related_items(parent, child)

        browser.login().visit(parent)
        Workflow().do_transition('publish')
        self.assertItemsEqual(
            ['The referenced object <a href="http://nohost/plone'
             '/parent/child">Child</a> is not yet published.'],
            statusmessages.warning_messages(),
        )

    @browsing
    def test_warning_not_shown_when_referencing_children_without_workflow(self, browser):
        parent = create(Builder('folder').titled(u'Parent'))
        child = create(Builder('file').titled(u'Child').within(parent))
        helpers.set_related_items(parent, child)

        browser.login().visit(parent)
        Workflow().do_transition('publish')
        self.assertItemsEqual(
            [],
            statusmessages.warning_messages(),
        )

    @browsing
    def test_do_not_fail_if_reference_is_none(self, browser):
        page = create(Builder('page')
                      .titled(u'The Page'))
        other_page = create(Builder('page')
                            .titled(u'The Other Page'))
        helpers.set_related_items(page, other_page)

        self.portal._delObject(other_page.getId(), suppress_events=True)
        transaction.commit()

        browser.login().visit(page)
        Workflow().do_transition('publish')
        statusmessages.assert_no_error_messages()

    @browsing
    def test_warning_on_publish_when_ftw_simplelayout_block_has_unpublished_references(self, browser):
        page = create(Builder('sl content page'))
        other_page = create(Builder('sl content page').titled(u'Other Page'))
        other_page_uuid = IUUID(other_page)
        textblock = create(Builder('sl textblock')
                           .having(text=RichTextValue('<a href="resolveuid/%s">link</a>' % other_page_uuid))
                           .within(page))

        notify(ObjectModifiedEvent(textblock))
        transaction.commit()

        browser.login().visit(page)
        Workflow().do_transition('publish')

        statusmessages.assert_message(
            'The referenced object <a href="http://nohost/plone'
            '/other-page">Other Page</a> is not yet published.'
        )

    @browsing
    def test_no_warning_on_publish_when_page_content_has_reference_to_itself(self, browser):
        page = create(Builder('sl content page'))
        create(Builder('sl textblock')
               .having(text=RichTextValue('<a href="resolveuid/%s">link</a>' % IUUID(page)))
               .within(page))

        browser.login().visit(page)
        Workflow().do_transition('publish')

        self.assertFalse(
            statusmessages.warning_messages(),
            'A reference in the page to itself should not return an error on '
            'publication.')

    @browsing
    def test_no_warning_on_publish_when_page_content_has_reference_to_content_without_workflow_on_page(self, browser):
        page = create(Builder('sl content page'))
        textblock = create(Builder('sl textblock')
                          .within(page))
        create(Builder('sl textblock')
               .having(text=RichTextValue('<a href="resolveuid/%s">link</a>' % IUUID(textblock)))
               .within(page))

        browser.login().visit(page)
        Workflow().do_transition('publish')

        self.assertFalse(
            statusmessages.warning_messages(),
            'A reference in the page to another object in itself should not '
            'return an error on publication.')

    @browsing
    def test_warning_on_publish_when_page_content_has_reference_to_content_on_other_page(self, browser):
        target_page = create(Builder('sl content page').titled(u'Target'))
        target_textblock = create(Builder('sl textblock').within(target_page)
                                  .titled(u'Target Block'))

        source_page = create(Builder('sl content page').titled(u'Source'))
        source_textblock = create(Builder('sl textblock')
                                  .titled(u'Source Block')
                                  .having(text=RichTextValue('<a href="resolveuid/%s">link</a>' % IUUID(target_textblock)))
                                  .within(source_page))

        notify(ObjectModifiedEvent(source_textblock))
        transaction.commit()

        browser.login().visit(source_page)
        Workflow().do_transition('publish')

        statusmessages.assert_message('The referenced object <a href="{}">Target</a> is not yet published.'.format(
            target_page.absolute_url()))

    @browsing
    def test_warning_on_retract_when_references_are_still_published(self, browser):
        page = create(Builder('page')
                      .titled(u'The Page'))
        other_page = create(Builder('page')
                            .titled(u'The Other Page'))
        helpers.set_related_items(page, other_page)

        api.content.transition(obj=page, to_state=EXAMPLE_WF_PUBLISHED)
        api.content.transition(obj=other_page, to_state=EXAMPLE_WF_PUBLISHED)
        transaction.commit()

        browser.login().visit(page)
        Workflow().do_transition('retract')

        statusmessages.assert_message(
            'The referenced object <a href="http://nohost/plone'
            '/the-other-page">The Other Page</a> is still published.'
        )

    @browsing
    def test_warning_on_retract_when_ftw_simplelayout_block_has_published_references(self, browser):
        page = create(Builder('sl content page'))
        other_page = create(Builder('sl content page')
                            .titled(u'Other Page')
                            .in_state(EXAMPLE_WF_PUBLISHED))
        other_page_uuid = IUUID(other_page)
        textblock = create(Builder('sl textblock')
                           .having(text=RichTextValue('<a href="resolveuid/%s">link</a>' % other_page_uuid))
                           .within(page))

        notify(ObjectModifiedEvent(textblock))
        transaction.commit()

        browser.login().visit(page)
        # cannot add text block when published
        Workflow().do_transition('publish')
        Workflow().do_transition('retract')

        statusmessages.assert_message(
            'The referenced object <a href="http://nohost/plone'
            '/other-page">Other Page</a> is still published.'
        )
