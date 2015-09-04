from ftw.builder.testing import BUILDER_LAYER
from ftw.builder.testing import functional_session_factory
from ftw.builder.testing import set_builder_session_factory
from ftw.testing import ComponentRegistryLayer
from ftw.testing import FunctionalSplinterTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.testing import z2
from zope.configuration import xmlconfig
import ftw.publisher.sender.tests.builders


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

        z2.installProduct(app, 'ftw.contentpage')
        z2.installProduct(app, 'simplelayout.base')
        z2.installProduct(app, 'simplelayout.ui.base')
        z2.installProduct(app, 'simplelayout.ui.dragndrop')
        z2.installProduct(app, 'ftw.simplelayout')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'ftw.contentpage:default')
        applyProfile(portal, 'ftw.simplelayout.contenttypes:default')
        applyProfile(portal, 'ftw.publisher.sender:default')
        applyProfile(portal, 'ftw.publisher.sender:example-workflow')


PUBLISHER_SENDER_FIXTURE = PublisherSenderLayer()
PUBLISHER_SENDER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PUBLISHER_SENDER_FIXTURE,),
    name="ftw.publisher.sender:integration")

PUBLISHER_SENDER_FUNCTIONAL_TESTING = FunctionalSplinterTesting(
    bases=(PUBLISHER_SENDER_FIXTURE,
           set_builder_session_factory(functional_session_factory)),
    name="ftw.publisher.sender:functional")
