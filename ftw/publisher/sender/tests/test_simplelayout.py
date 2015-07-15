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


class TestPublishingSimplelayoutTypes(TestCase):

    layer = PUBLISHER_SENDER_FUNCTIONAL_TESTING

    portal_type = 'ContentPage'
    page_builder = 'content page'
    textblock_builder = 'text block'
    listingblock_builder = 'listing block'

    def setUp(self):
        super(TestPublishingSimplelayoutTypes, self).setUp()

        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.setChainForPortalTypes([self.portal_type],
                                      'publisher-example-workflow')

    def test_blocks_are_published_with_contentpage(self):
        page = create(Builder(self.page_builder))
        create(Builder(self.textblock_builder).within(page))

        Plone().login().visit(page)
        Workflow().do_transition('publish')

        queue = IQueue(self.portal)
        self.assertEquals(
            2, queue.countJobs(),
            'Expected the page and the text block to be in the queue.')

    def test_sl_listing_block_publishes_its_children(self):
        page = create(Builder(self.page_builder))
        listing_block = create(Builder(self.listingblock_builder).within(page))
        create(Builder('file').within(listing_block))

        Plone().login().visit(page)
        Workflow().do_transition('publish')

        queue = IQueue(self.portal)
        self.assertEquals(
            3, queue.countJobs(),
            'Expected the page, the listing block and the file to be'
            ' in the queue.')


class TestPublishingNEWSimplelayoutTypes(TestPublishingSimplelayoutTypes):

    portal_type = 'ftw.simplelayout.ContentPage'
    page_builder = 'sl content page'
    textblock_builder = 'sl textblock'
    listingblock_builder = 'sl listingblock'
