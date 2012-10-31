from zope import interface
from zope.component.interfaces import IObjectEvent
from zope.viewlet.interfaces import IViewletManager


class IConfig(interface.Interface):
    """
    Marker Interface for the Config adapter.
    See persistence.py
    """


class IQueue(interface.Interface):
    """
    Marker Interface for the Queue adapter
    See persistence.py
    """


class IAfterPushEvent(IObjectEvent):
    """
    Event gets fired, after object is pushed to the realm
    """


class IQueueExecutedEvent(IObjectEvent):
    """The queue was executed successfully.
    The event is fired on the portal object.
    """


class IBeforeQueueExecutionEvent(IObjectEvent):
    """The `BeforeQueueExecutionEvent` is fired before
    executing a queue. Be aware that the transaction may
    be aborted if there is an error.
    """


class IPathBlacklist(interface.Interface):
    """ Adapter interface for the PathBlacklist adapter which
    knows if the object is blacklisted.
    """

    def is_blacklisted(self, context=None, path=None):
        """ Checks if the adapter the context, the given
        `context` or the given `path` is blacklisted.
        """


class IConfigletViewletManager(IViewletManager):
    """Viewlet manager for the ftw.publisher.sender configlet. It can be
    used by plugins to make themselves configurable within the default
    configlet.

    """