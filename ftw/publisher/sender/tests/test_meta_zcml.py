from Products.CMFPlone.interfaces import IPloneSiteRoot
from ftw.publisher.sender.interfaces import IConfig
from ftw.publisher.sender.interfaces import IOverriddenRealmRegistry
from ftw.publisher.sender.interfaces import IRealm
from ftw.publisher.sender.persistence import Realm
from ftw.publisher.sender.testing import ZCML_LAYER
from ftw.testing import MockTestCase
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.component import queryUtility


class TestOverriddenRealmZCML(MockTestCase):

    layer = ZCML_LAYER

    def test_no_overridden_realm_registry_by_default(self):
        self.assertFalse(queryUtility(IOverriddenRealmRegistry))

    def test_simple_overridden_realm(self):
        self.layer.load_zcml_string(
            '\n'.join((
                    '<configure xmlns:publisher="http://namespaces.' + \
                        'zope.org/ftw.publisher">',

                    '    <publisher:override-realm',
                    '        url="http://localhost:9090/site"',
                    '        username="publisher-user"',
                    '        password="publisher-password" />',

                    '</configure>'
                    )))

        registry = queryUtility(IOverriddenRealmRegistry)
        self.assertTrue(registry)

        self.assertEquals(len(registry.realms), 1,
                          'Not exactly one realm registerd, as expected')

        realm = registry.realms[0]
        self.assertTrue(IRealm.providedBy(realm))

        self.assertTrue(realm.active)
        self.assertEquals(realm.url, 'http://localhost:9090/site')
        self.assertEquals(realm.username, 'publisher-user')
        self.assertEquals(realm.password, 'publisher-password')

    def test_multiple_override_realms(self):
        self.layer.load_zcml_string(
            '\n'.join((
                    '<configure xmlns:publisher="http://namespaces.' + \
                        'zope.org/ftw.publisher">',

                    '    <publisher:override-realm',
                    '        url="http://localhost:9090/site-1"',
                    '        username="publisher-user"',
                    '        password="publisher-password" />',

                    '    <publisher:override-realm',
                    '        url="http://localhost:9090/site-2"',
                    '        username="publisher-user"',
                    '        password="publisher-password" />',

                    '</configure>'
                    )))

        registry = queryUtility(IOverriddenRealmRegistry)
        self.assertTrue(registry)

        self.assertEquals(len(registry.realms), 2,
                          'Not exactly two realm registerd, as expected')

        one, two = registry.realms
        self.assertEquals(one.url, 'http://localhost:9090/site-1')
        self.assertEquals(two.url, 'http://localhost:9090/site-2')

    def test_inactive_realm(self):
        self.layer.load_zcml_string(
            '\n'.join((
                    '<configure xmlns:publisher="http://namespaces.' + \
                        'zope.org/ftw.publisher">',

                    '    <publisher:override-realm',
                    '        active="false"'
                    '        url="http://localhost:9090/site"',
                    '        username="publisher-user"',
                    '        password="publisher-password" />',

                    '</configure>'
                    )))

        registry = queryUtility(IOverriddenRealmRegistry)
        self.assertTrue(registry)

        self.assertEquals(len(registry.realms), 1,
                          'Not exactly one realm registerd, as expected')

        realm = registry.realms[0]
        self.assertTrue(IRealm.providedBy(realm))

        self.assertFalse(realm.active)

    def test_default_realms_config(self):
        portal = self.providing_stub([IPloneSiteRoot, IAttributeAnnotatable])
        self.expect(portal.portal_url.getPortalObject()).result(portal)
        self.replay()

        config = IConfig(portal)
        self.assertTrue(config)
        self.assertTrue(config.is_update_realms_possible())

        self.assertEquals(len(config.getRealms()), 0)
        config.appendRealm(Realm(1, 'http://site', 'foo', 'pw'))
        self.assertEquals(len(config.getRealms()), 1)

    def test_overridden_realms_config(self):
        self.layer.load_zcml_string(
            '\n'.join((
                    '<configure xmlns:publisher="http://namespaces.' + \
                        'zope.org/ftw.publisher">',

                    '    <publisher:override-realm',
                    '        url="http://localhost:9090/site"',
                    '        username="publisher-user"',
                    '        password="publisher-password" />',

                    '</configure>'
                    )))

        portal = self.providing_stub([IPloneSiteRoot, IAttributeAnnotatable])
        self.expect(portal.portal_url.getPortalObject()).result(portal)
        self.replay()

        config = IConfig(portal)
        self.assertTrue(config)
        self.assertFalse(config.is_update_realms_possible())

        self.assertEquals(len(config.getRealms()), 1)

        with self.assertRaises(AttributeError):
            config.appendRealm(Realm(1, 'http://site', 'foo', 'pw'))
