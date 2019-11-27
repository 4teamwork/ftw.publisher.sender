from ftw.builder.testing import BUILDER_LAYER
from ftw.builder.testing import functional_session_factory
from ftw.builder.testing import set_builder_session_factory
from ftw.publisher.sender.utils import IS_AT_LEAST_PLONE_5_1
from ftw.publisher.sender.utils import IS_PLONE_4
from ftw.testing import ComponentRegistryLayer
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2
from zope.configuration import xmlconfig
import ftw.publisher.sender.tests.builders  # noqa


class ZCMLLayer(ComponentRegistryLayer):

    def setUp(self):
        super(ZCMLLayer, self).setUp()

        import ftw.publisher.sender.tests
        self.load_zcml_file('tests.zcml', ftw.publisher.sender.tests)


ZCML_LAYER = ZCMLLayer()


class PublisherSenderLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, BUILDER_LAYER)

    def setUpZope(self, app, configurationContext):
        xmlconfig.string(
            '<configure xmlns="http://namespaces.zope.org/zope">'
            '  <include package="z3c.autoinclude" file="meta.zcml" />'
            '  <includePlugins package="plone" />'
            '  <includePluginsOverrides package="plone" />'
            '</configure>',
            context=configurationContext)

        z2.installProduct(app, 'ftw.simplelayout')
        z2.installProduct(app, 'Products.PloneFormGen')
        import plone.app.dexterity
        xmlconfig.file('configure.zcml', plone.app.dexterity,
                       context=configurationContext)

        import ftw.publisher.sender.tests
        xmlconfig.file('profiles/dexterity.zcml', ftw.publisher.sender.tests,
                       context=configurationContext)

    def setUpPloneSite(self, portal):
        if IS_PLONE_4:
            applyProfile(portal, 'plone.app.referenceablebehavior:default')

        applyProfile(portal, 'ftw.simplelayout.contenttypes:default')
        applyProfile(portal, 'ftw.publisher.sender:default')
        applyProfile(portal, 'ftw.publisher.sender:example-workflow')
        applyProfile(portal, 'plone.app.relationfield:default')
        applyProfile(portal, 'ftw.publisher.sender.tests:dexterity')
        applyProfile(portal, 'Products.PloneFormGen:default')

        if IS_PLONE_4:
            applyProfile(portal, 'ftw.publisher.sender.tests:dexterity-plone4')

        if IS_AT_LEAST_PLONE_5_1:
            applyProfile(portal, 'plone.app.contenttypes:default')


PUBLISHER_SENDER_FIXTURE = PublisherSenderLayer()
PUBLISHER_SENDER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PUBLISHER_SENDER_FIXTURE,),
    name="ftw.publisher.sender:integration")

PUBLISHER_SENDER_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PUBLISHER_SENDER_FIXTURE,
           set_builder_session_factory(functional_session_factory)),
    name="ftw.publisher.sender:functional")
