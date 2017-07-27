from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from unittest2 import TestCase
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
        which would import from ftw.contentpage builders and other dependencies
        which may not be installed.
        """
        from ftw.publisher.sender import testing
        return testing.PUBLISHER_SENDER_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

    def grant(self, *roles):
        setRoles(self.portal, TEST_USER_ID, list(roles))
        transaction.commit()
