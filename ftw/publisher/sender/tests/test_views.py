from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.sender.interfaces import IQueue
from ftw.publisher.sender.tests import FunctionalTestCase
from ftw.testbrowser import browsing
from ftw.testbrowser.pages import statusmessages
import transaction


class TestPublishObjectView(FunctionalTestCase):

    @browsing
    def test_publish_folder_enqueues_job(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder'))
        transaction.commit()

        self.assertEquals(0, IQueue(self.portal).countJobs())
        browser.login().open(folder, view='@@publisher.publish')
        statusmessages.assert_message('This object has been added to the queue.')
        transaction.begin()

        self.assertEquals(1, IQueue(self.portal).countJobs())
        job = IQueue(self.portal).getJobs()[0]
        self.assertEquals('push', job.action)
        self.assertEquals(folder, job.getObject(self.portal))

    @browsing
    def test_publish_plonesite_enqueues_job(self, browser):
        self.grant('Manager')
        self.assertEquals(0, IQueue(self.portal).countJobs())
        browser.login().open(self.portal, view='@@publisher.publish')
        statusmessages.assert_message('This object has been added to the queue.')
        transaction.begin()

        self.assertEquals(1, IQueue(self.portal).countJobs())
        job = IQueue(self.portal).getJobs()[0]
        self.assertEquals('push', job.action)
        self.assertEquals(self.portal, job.getObject(self.portal))


class TestDeleteObjectView(FunctionalTestCase):

    @browsing
    def test_delete_folder_enqueues_job(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder'))
        transaction.commit()

        self.assertEquals(0, IQueue(self.portal).countJobs())
        browser.login().open(folder, view='@@publisher.delete')
        statusmessages.assert_message('This object will be deleted at the remote sites.')
        transaction.begin()

        self.assertEquals(1, IQueue(self.portal).countJobs())
        job = IQueue(self.portal).getJobs()[0]
        self.assertEquals('delete', job.action)
        self.assertEquals(folder, job.getObject(self.portal))

    @browsing
    def test_delete_plonesite_is_not_allowed(self, browser):
        self.grant('Manager')
        self.assertEquals(0, IQueue(self.portal).countJobs())
        with browser.expect_http_error(500):
            browser.login().open(self.portal, view='@@publisher.delete')
