from ftw.publisher.sender.interfaces import IAfterPushEvent
from ftw.publisher.sender.interfaces import IBeforeQueueExecutionEvent
from ftw.publisher.sender.interfaces import IQueueExecutedEvent
from zope import interface
from zope.component.interfaces import ObjectEvent


class AfterPushEvent(ObjectEvent):
    interface.implements(IAfterPushEvent)

    def __init__(self, context, state, job):
        ObjectEvent.__init__(self, context)
        self.action = job.action
        self.title = job.objectTitle
        self.path = job.objectPath
        self.uid = job.objectUID

        self.state = state


class BeforeQueueExecutionEvent(ObjectEvent):
    """The `BeforeQueueExecutionEvent` is fired before
    executing a queue. Be aware that the transaction may
    be aborted if there is an error.
    """

    interface.implements(IBeforeQueueExecutionEvent)

    def __init__(self, context, queue):
        ObjectEvent.__init__(self, context)
        self.queue = queue


class QueueExecutedEvent(ObjectEvent):
    """The queue was executed successfully.
    The event is fired on the portal object.
    """

    interface.implements(IQueueExecutedEvent)

    def __init__(self, context, log):
        ObjectEvent.__init__(self, context)
        self.log = log
