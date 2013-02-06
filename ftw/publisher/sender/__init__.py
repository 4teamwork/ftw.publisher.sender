from ftw.publisher.core.utils import getPublisherLogger, getPublisherErrorLogger
from zope.i18nmessageid import MessageFactory


message_factory = MessageFactory('ftw.publisher.sender')
_ = message_factory


def getLogger():
    """
    Returns the logger instance for the module ftw.publisher.sender
    @return: Logging instance
    """
    return getPublisherLogger('ftw.publisher.sender')


def getErrorLogger():
    """ Returns a error log instance, which loggs into the error log
    """
    return getPublisherErrorLogger('ftw.publisher.sender')
