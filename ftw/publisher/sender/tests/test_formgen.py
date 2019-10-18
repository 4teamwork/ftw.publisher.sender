from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.sender.interfaces import IConfig
from ftw.publisher.sender.persistence import Realm
from ftw.publisher.sender.tests import FunctionalTestCase
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Products.CMFCore.utils import getToolByName
from urllib2 import URLError
import transaction


class TestFormGenIntegration(FunctionalTestCase):

    def setUp(self):
        super(TestFormGenIntegration, self).setUp()

        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        self.wftool = getToolByName(self.portal, 'portal_workflow')
        self.wftool.setChainForPortalTypes(['FormFolder', 'Form Folder'],
                                           'publisher-example-workflow')

        self.formfolder = create(Builder('form folder'))
        self.save_data_adapter = create(Builder(
            'save data adapter').within(self.formfolder))

        self.data_string = "hans@muster.ch, Test, only a Test \n \
                           peter@muster.ch, another Test, Still a Test"

        self.save_data_adapter.setSavedFormInput(self.data_string)
        config = IConfig(self.portal)
        config.appendRealm(Realm(1, 'http://site', 'foo', 'pw'))

    def test_data_not_published(self):
        csv = self.save_data_adapter.download(self.portal.REQUEST,
                                              self.portal.REQUEST.RESPONSE)
        lines = csv.split('\r\n')
        self.assertIn("hans@muster.ch, Test, only a Test", lines[0])
        self.assertIn("peter@muster.ch, another Test, Still a Test", lines[1])

    def test_data_published(self):
        self.wftool.doActionFor(self.formfolder,
                                'publisher-example-workflow-'
                                '-TRANSITION--publish--internal_published')
        transaction.commit()
        with self.assertRaises(URLError):
            self.save_data_adapter.download(self.portal.REQUEST,
                                            self.portal.REQUEST.RESPONSE)

    def test_form_elements_are_published_along_with_form(self):
        self.assertEqual(['mailer', 'replyto', 'topic', 'comments', 'thank-you', 'formsavedataadapter'],
                         self.formfolder.contentIds())
        self.formfolder.restrictedTraverse('@@publisher.publish')()
        self.assert_jobs(('push', 'formfolder'),
                         ('push', 'mailer'),
                         ('push', 'replyto'),
                         ('push', 'topic'),
                         ('push', 'comments'),
                         ('push', 'thank-you'),
                         ('push', 'formsavedataadapter'))
