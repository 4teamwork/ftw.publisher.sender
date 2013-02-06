from ftw.publisher.sender.interfaces import IOverriddenRealmRegistry
from ftw.publisher.sender.interfaces import IRealm
from zope.component import getSiteManager
from zope.configuration.fields import Bool
from zope.interface import Interface
from zope.interface import implements
from zope.schema import TextLine
from zope.schema import URI


class IOverrideRealm(Interface):

    active = Bool(
        title=u'Active',
        required=False,
        default=True)

    url = URI(
        title=u'URL to the Plone-Site',
        required=True)

    username = TextLine(
        title=u'Zope username',
        required=True)

    password = TextLine(
        title=u'Zope password',
        required=True)


class OverriddenRealmRegistry(object):
    implements(IOverriddenRealmRegistry)

    def __init__(self):
        self.realms = []


class OverridenRealm(object):
    implements(IRealm)

    def __init__(self, url, username, password, active=True):
        self.active = active
        self.url = url
        self.username = username
        self.password = password


def register_realm_handler(realm_arguments):
    sm = getSiteManager()
    component = sm.queryUtility(IOverriddenRealmRegistry)

    if component is None:
        component = OverriddenRealmRegistry()
        provides = IOverriddenRealmRegistry
        name = ''

        sm.registerUtility(component, provides, name)

    component.realms.append(OverridenRealm(**realm_arguments))


def override_realm(_context, **kwargs):
    _context.action(
        discriminator=('override-realm', str(kwargs)),
        callable=register_realm_handler,
        args=(kwargs,))
