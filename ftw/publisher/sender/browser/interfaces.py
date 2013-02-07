from ftw.publisher.sender import message_factory as _
from ftw.publisher.sender.interfaces import IRealm
from zope import schema
from zope.interface import Interface


class IRealmSchema(IRealm):
    pass


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
