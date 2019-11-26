from ftw.publisher.sender.interfaces import IQueue
from path import Path
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from unittest import TestCase
import transaction


class FunctionalTestCase(TestCase):

    @property
    def layer(self):
        """The testing layer is implemented as a property so that we can defer the
        layer import.

        This is important for packages depending on ftw.publisher.sender and using
        the WorkflowConfigTest-class as superclass, without installing
        ftw.publisher.sender's tests-extras.

        If the layer import would be on module level, we would load the testing.py,
        which would import from dependencies which may not be installed.
        """
        from ftw.publisher.sender import testing
        return testing.PUBLISHER_SENDER_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

    def grant(self, *roles):
        setRoles(self.portal, TEST_USER_ID, list(roles))
        transaction.commit()

    def asset(self, filename):
        filepath = Path(__file__).parent.joinpath('assets', filename)
        assert filepath.isfile(), 'Missing asset "{0}" at {1}'.format(filepath, filepath)
        return filepath

    def assert_jobs(self, *expected):
        """Example:
        self.assert_jobs(('push', 'page'), ('push', 'textblock'))
        """
        got = []
        for job in IQueue(self.portal).getJobs():
            got.append((job.action, job.getObject(self.portal).getId()))

        self.assertEqual(list(expected), list(got))
