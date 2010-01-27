from zope.component.interfaces import ObjectEvent
from zope import interface
from interfaces import IAfterPushEvent


class AfterPushEvent(ObjectEvent):
    interface.implements(IAfterPushEvent)

    def __init__(self, context, state, job):
        ObjectEvent.__init__(self, context)
        self.action = job.action
        self.title = job.objectTitle
        self.path = job.objectPath
        self.uid = job.objectUID    
        
        self.state = state 

