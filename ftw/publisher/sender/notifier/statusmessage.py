from AccessControl.SecurityInfo import ClassSecurityInformation
from Products.statusmessages.interfaces import IStatusMessage

class set_statusmessage(object):
    security = ClassSecurityInformation()

    def __init__(self, context, event):
        IStatusMessage(event.request).addStatusMessage(
            u'Object with Title: %s has been %s on %s' % (event.title.decode('utf-8'),
                                                          event.state.toString().decode('utf-8'),
                                                          event.path.decode('utf-8')),
            type='info'
            )
