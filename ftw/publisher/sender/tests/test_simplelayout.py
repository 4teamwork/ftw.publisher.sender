from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.sender.interfaces import IQueue
from ftw.publisher.sender.tests import FunctionalTestCase
from ftw.publisher.sender.tests.pages import Workflow
from ftw.publisher.sender.utils import IS_AT_LEAST_PLONE_5_1
from ftw.simplelayout.configuration import flattened_block_uids
from ftw.simplelayout.interfaces import IPageConfiguration
from ftw.testbrowser import browsing
from ftw.testing import staticuid
from unittest2 import skipIf
from Products.CMFCore.utils import getToolByName


@skipIf(IS_AT_LEAST_PLONE_5_1, 'ftw.contentpage is not available for Plone 5')
class TestPublishingFtwContentpageTypes(FunctionalTestCase):

    portal_type = 'ContentPage'
    page_builder = 'content page'
    textblock_builder = 'text block'
    listingblock_builder = 'listing block'

    def setUp(self):
        super(TestPublishingFtwContentpageTypes, self).setUp()
        self.grant('Manager')

        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.setChainForPortalTypes([self.portal_type],
                                      'publisher-example-workflow')

    @browsing
    def test_blocks_are_published_with_contentpage(self, browser):
        page = create(Builder(self.page_builder))
        create(Builder(self.textblock_builder).within(page))

        browser.login().visit(page)
        Workflow().do_transition('publish')

        queue = IQueue(self.portal)
        self.assertEquals(
            2, queue.countJobs(),
            'Expected the page and the text block to be in the queue.')

    @browsing
    def test_sl_listing_block_publishes_its_children(self, browser):
        page = create(Builder(self.page_builder))
        listing_block = create(Builder(self.listingblock_builder).within(page))
        create(Builder('file').within(listing_block))

        browser.login().visit(page)
        Workflow().do_transition('publish')

        queue = IQueue(self.portal)
        self.assertEquals(
            3, queue.countJobs(),
            'Expected the page, the listing block and the file to be'
            ' in the queue.')


class TestPublishingFtwSimplelayoutTypes(FunctionalTestCase):

    portal_type = 'ftw.simplelayout.ContentPage'
    page_builder = 'sl content page'
    textblock_builder = 'sl textblock'
    listingblock_builder = 'sl listingblock'

    def setUp(self):
        super(TestPublishingFtwSimplelayoutTypes, self).setUp()
        self.grant('Manager')

        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.setChainForPortalTypes([self.portal_type],
                                      'publisher-example-workflow')

    @browsing
    def test_blocks_are_published_with_contentpage(self, browser):
        page = create(Builder(self.page_builder))
        create(Builder(self.textblock_builder).within(page))

        browser.login().visit(page)
        Workflow().do_transition('publish')

        queue = IQueue(self.portal)
        self.assertEquals(
            2, queue.countJobs(),
            'Expected the page and the text block to be in the queue.')

    @browsing
    def test_sl_listing_block_publishes_its_children(self, browser):
        page = create(Builder(self.page_builder))
        listing_block = create(Builder(self.listingblock_builder).within(page))
        create(Builder('file').within(listing_block))

        browser.login().visit(page)
        Workflow().do_transition('publish')

        queue = IQueue(self.portal)
        self.assertEquals(
            3, queue.countJobs(),
            'Expected the page, the listing block and the file to be'
            ' in the queue.')

    def test_no_delete_jobs_for_blocks(self):
        """When a block is deleted, we do not want to instantly delete
        the block on the receiver side.
        Instead the block is deleted automatically when the page is published
        because it is no longer listed in the page state.
        """

        page = create(Builder(self.page_builder))
        textblock = create(Builder(self.textblock_builder).within(page))

        self.assertEquals(0, IQueue(self.portal).countJobs())
        page.manage_delObjects([textblock.getId()])
        self.assertEquals(0, IQueue(self.portal).countJobs(),
                          'Deleting an ftw.simplelayout block'
                          ' should not publish a delete job.')

        self.portal.manage_delObjects([page.getId()])
        self.assertEquals(1, IQueue(self.portal).countJobs(),
                          'Deleteing an ftw.simplelayout page'
                          ' should still add a delete job.')

    @staticuid('staticuid')
    def test_syncs_pagestate_before_publishing(self):
        page = create(Builder('sl content page'))
        create(Builder('sl textblock').within(page))
        self.assertEquals([], flattened_block_uids(IPageConfiguration(page).load()))

        page.restrictedTraverse('@@publisher.publish')()
        self.assertEquals(['staticuid00000000000000000000002'],
                          flattened_block_uids(IPageConfiguration(page).load()))
