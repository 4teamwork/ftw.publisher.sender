from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.sender.interfaces import IPreventPublishing
from ftw.publisher.sender.interfaces import IQueue
from ftw.publisher.sender.nojobs import publisher_jobs_disabled
from ftw.publisher.sender.testing import PUBLISHER_SENDER_FUNCTIONAL_TESTING
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from unittest2 import TestCase


class TestNoJobs(TestCase):
    layer = PUBLISHER_SENDER_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

    def test_publish(self):
        page = create(Builder('page'))
        queue = IQueue(self.portal)
        self.assertEquals(0, queue.countJobs())

        with publisher_jobs_disabled():
            page.restrictedTraverse('@@publisher.publish')()
        self.assertEquals(0, queue.countJobs())

        page.restrictedTraverse('@@publisher.publish')()
        self.assertEquals(1, queue.countJobs())

    def test_delete(self):
        page = create(Builder('page'))
        queue = IQueue(self.portal)
        self.assertEquals(0, queue.countJobs())

        with publisher_jobs_disabled():
            page.restrictedTraverse('@@publisher.delete')()
        self.assertEquals(0, queue.countJobs())

        page.restrictedTraverse('@@publisher.delete')()
        self.assertEquals(1, queue.countJobs())


class TestPreventPublishing(TestCase):
    layer = PUBLISHER_SENDER_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

    def test_publish(self):
        page = create(Builder('page').providing(IPreventPublishing))
        queue = IQueue(self.portal)
        self.assertEquals(0, queue.countJobs())

        page.restrictedTraverse('@@publisher.publish')()
        self.assertEquals(0, queue.countJobs())

    def test_delete(self):
        page = create(Builder('page').providing(IPreventPublishing))
        queue = IQueue(self.portal)
        self.assertEquals(0, queue.countJobs())

        page.restrictedTraverse('@@publisher.delete')()
        self.assertEquals(0, queue.countJobs())
