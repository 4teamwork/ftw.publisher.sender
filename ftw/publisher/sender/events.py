from zope.component.interfaces import ObjectEvent
from zope import interface
from interfaces import IAfterPushEvent, IQueueExecutedEvent


class AfterPushEvent(ObjectEvent):
    interface.implements(IAfterPushEvent)

    def __init__(self, context, state, job):
        ObjectEvent.__init__(self, context)
        self.action = job.action
        self.title = job.objectTitle
        self.path = job.objectPath
        self.uid = job.objectUID    
        
        self.state = state 


class QueueExecutedEvent(ObjectEvent):
    """The queue was executed successfully.
    The event is fired on the portal object.
    """

    interface.implements(IQueueExecutedEvent)

    def __init__(self, portal, log):
        self.portal = self.context = portal
        self.log = log
