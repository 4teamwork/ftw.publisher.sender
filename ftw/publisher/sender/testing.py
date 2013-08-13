from ftw.builder.testing import BUILDER_LAYER
from ftw.builder.testing import functional_session_factory
from ftw.builder.testing import set_builder_session_factory
from ftw.testing import ComponentRegistryLayer
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from zope.configuration import xmlconfig


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

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'ftw.publisher.sender:default')
        applyProfile(portal, 'ftw.publisher.sender:example-workflow')


PUBLISHER_SENDER_FIXTURE = PublisherSenderLayer()
PUBLISHER_SENDER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PUBLISHER_SENDER_FIXTURE,
           set_builder_session_factory(functional_session_factory)),
    name="ftw.publisher.sender:integration")
