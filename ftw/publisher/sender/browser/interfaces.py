from ftw.publisher.sender import message_factory as _
from zope import schema
from zope.interface import Interface


class IRealmSchema(Interface):
    active = schema.Bool(
        title=_(u'label_realm_active',
                default=u'Active'))

    url = schema.URI(
        title=_(u'label_realm_url',
                u'URL to the Plone-Site'))

    username = schema.TextLine(
        title=_(u'label_realm_username',
                u'Username'))

    password = schema.Password(
        title=_(u'label_realm_password',
                u'Password'))


class IEditRealmSchema(IRealmSchema):

    id = schema.TextLine(
        title = u'id')

    password = schema.Password(
        title=_(u'label_realm_password',
                u'Password'),
        required = False)


class IBlacklistPathSchema(Interface):

    path = schema.TextLine(
        title = _(u'label_path',
                  default=u'Path'),
        required=True)
