from datetime import datetime
from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.sender.interfaces import IQueue
from ftw.publisher.sender.tests import FunctionalTestCase
from ftw.publisher.sender.utils import IS_AT_LEAST_PLONE_5_1
from ftw.testbrowser import browsing
from ftw.testbrowser.pages import statusmessages
from ftw.testing import freeze
from ftw.testing import staticuid
from plone.protect.authenticator import createToken
from plone.uuid.interfaces import IUUID
from unittest import skipUnless
from zope.component import getMultiAdapter
import json


class TestMove(FunctionalTestCase):

    @browsing
    @staticuid()
    def test_moving_object_job_data(self, browser):
        self.grant('Manager')
        source = create(Builder('folder').titled(u'Source'))
        target = create(Builder('folder').titled(u'Target'))
        with freeze(datetime(2018, 1, 2, 3, 4, 5)):
            page = create(Builder('page').titled(u'The Page').within(source))

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

        expected = {
            u'utf8:metadata': {
                u'utf8:UID': u'utf8:testmovingobjectjobdata000000003',
                u'utf8:action': u'utf8:move',
                u'utf8:id': u'utf8:the-page',
                u'utf8:modified': u'utf8:2018/01/02 03:04:05 GMT+1',
                u'utf8:physicalPath': u'utf8:/target/the-page',
                u'utf8:portal_type': u'utf8:Document',
                u'utf8:review_state': u'utf8:',
                u'utf8:sibling_positions': {u'utf8:the-page': 0}},
            u'utf8:move': {
                u'utf8:newName': u'utf8:the-page',
                u'utf8:newParent': u'utf8:/target',
                u'utf8:newTitle': u'unicode:The Page',
                u'utf8:oldName': u'utf8:the-page',
                u'utf8:oldParent': u'utf8:/source'}}

        if IS_AT_LEAST_PLONE_5_1:
            expected[u'utf8:metadata'][u'utf8:modified'] = u'utf8:{}'.format(
                str(page.modified()).decode('utf-8'))

        self.assertEquals(
            expected,
            json.loads(data))

    @browsing
    @staticuid()
    @skipUnless(IS_AT_LEAST_PLONE_5_1, 'object_rename only exists in Plone 5.x')
    def test_renaming_object_via_object_rename_action(self, browser):

        self.grant('Manager')
        folder = create(Builder('folder').titled(u'Folder'))
        with freeze(datetime(2018, 1, 2, 3, 4, 5)):
            page = create(Builder('page').titled(u'The Page').within(folder))

            self.assertEquals(0, IQueue(self.portal).countJobs())
            browser.login().open(page).click_on('Rename')
            browser.fill({'form.widgets.new_id': 'new_id'}).submit()
            statusmessages.assert_message(
                'Object move/rename action has been added to the queue.')

        self.assertEquals(1, IQueue(self.portal).countJobs())

        job, = IQueue(self.portal).getJobs()
        self.assertEquals('move', job.action)
        data = job.getData()
        self.assertTrue(data)

        self.maxDiff = None

        expected = {
            u'utf8:metadata': {
                u'utf8:UID': u'utf8:testrenamingobjectviaobjec000002',
                u'utf8:action': u'utf8:move',
                u'utf8:id': u'utf8:new_id',
                u'utf8:modified': u'utf8:2018/01/02 03:04:05 GMT+1',
                u'utf8:physicalPath': u'utf8:/folder/new_id',
                u'utf8:portal_type': u'utf8:Document',
                u'utf8:review_state': u'utf8:',
                u'utf8:sibling_positions': {u'utf8:new_id': 0}},
            u'utf8:move': {
                u'utf8:newName': u'utf8:new_id',
                u'utf8:newParent': u'utf8:/folder',
                u'utf8:newTitle': u'unicode:The Page',
                u'utf8:oldName': u'utf8:the-page',
                u'utf8:oldParent': u'utf8:/folder'}}

        if IS_AT_LEAST_PLONE_5_1:
            expected[u'utf8:metadata'][u'utf8:modified'] = u'utf8:{}'.format(
                str(page.modified()).decode('utf-8'))

        self.assertEquals(
            expected,
            json.loads(data))

    @browsing
    @staticuid()
    @skipUnless(IS_AT_LEAST_PLONE_5_1, 'object_rename only exists in Plone 5.x')
    def test_renaming_object_via_folder_contents_rename_action(self, browser):

        self.grant('Manager')
        folder = create(Builder('folder').titled(u'Folder'))
        with freeze(datetime(2018, 1, 2, 3, 4, 5)):
            page = create(Builder('page').titled(u'The Page').within(folder))

            self.assertEquals(0, IQueue(self.portal).countJobs())

            form_data = {}
            form_data['_authenticator'] = createToken()
            form_data['UID_1'] = IUUID(page)
            form_data['newid_1'] = 'new_id'
            form_data['newtitle_1'] = u'Ch\xe4nged title'

            browser.login().visit(folder, view='@@fc-rename', data=form_data)

        self.assertEquals(1, IQueue(self.portal).countJobs())

        job, = IQueue(self.portal).getJobs()
        self.assertEquals('move', job.action)
        data = job.getData()
        self.assertTrue(data)

        self.maxDiff = None

        expected = {
            u'utf8:metadata': {
                u'utf8:UID': u'utf8:testrenamingobjectviafolde000002',
                u'utf8:action': u'utf8:move',
                u'utf8:id': u'utf8:new_id',
                u'utf8:modified': u'utf8:2018/01/02 03:04:05 GMT+1',
                u'utf8:physicalPath': u'utf8:/folder/new_id',
                u'utf8:portal_type': u'utf8:Document',
                u'utf8:review_state': u'utf8:',
                u'utf8:sibling_positions': {u'utf8:new_id': 0}},
            u'utf8:move': {
                u'utf8:newName': u'utf8:new_id',
                u'utf8:newParent': u'utf8:/folder',
                u'utf8:newTitle': u'unicode:Ch\xe4nged title',
                u'utf8:oldName': u'utf8:the-page',
                u'utf8:oldParent': u'utf8:/folder'}}

        if IS_AT_LEAST_PLONE_5_1:
            expected[u'utf8:metadata'][u'utf8:modified'] = u'utf8:{}'.format(
                str(page.modified()).decode('utf-8'))

        self.assertEquals(
            expected,
            json.loads(data))
