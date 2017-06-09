from datetime import datetime
from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.sender.interfaces import IQueue
from ftw.publisher.sender.tests import FunctionalTestCase
from ftw.testbrowser import browsing
from ftw.testbrowser.pages import statusmessages
from ftw.testing import freeze
from ftw.testing import staticuid
import json


class TestMove(FunctionalTestCase):

    @browsing
    @staticuid()
    def test_moving_object_job_data(self, browser):
        self.grant('Manager')
        source = create(Builder('folder').titled(u'Source'))
        target = create(Builder('folder').titled(u'Target'))
        with freeze(datetime(2018, 1, 2, 3, 4, 5)):
            page = create(Builder('page').titled('The Page').within(source))

        self.assertEquals(0, IQueue(self.portal).countJobs())
        browser.login().open(page).click_on('Cut').open(target).click_on('Paste')
        statusmessages.assert_message(
            'Object move/rename action has been added to the queue.')

        self.assertEquals(1, IQueue(self.portal).countJobs())

        job, = IQueue(self.portal).getJobs()
        self.assertEquals('move', job.action)
        data = job.getData()
        self.assertTrue(data)

        self.maxDiff = None
        self.assertEquals(
            {u'utf8:metadata': {
                u'utf8:UID': u'utf8:testmovingobjectjobdata000000003',
                u'utf8:action': u'utf8:move',
                u'utf8:id': u'utf8:the-page',
                u'utf8:modified': u'utf8:2018/01/02 03:04:05 GMT+1',
                u'utf8:physicalPath': u'utf8:/target/the-page',
                u'utf8:portal_type': u'utf8:Document',
                u'utf8:review_state': u'utf8:',
                u'utf8:schema_path': u'utf8:Products.ATContentTypes.content.document.ATDocument.schema',
                u'utf8:sibling_positions': {u'utf8:the-page': 0}},
             u'utf8:move': {
                 u'utf8:newName': u'utf8:the-page',
                 u'utf8:newParent': u'utf8:/target',
                 u'utf8:newTitle': u'unicode:The Page',
                 u'utf8:oldName': u'utf8:the-page',
                 u'utf8:oldParent': u'utf8:/source'}},
            json.loads(data))
