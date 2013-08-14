from ftw.publisher.sender.utils import is_temporary
from ftw.publisher.sender.workflows.interfaces import DELETE_ACTIONS
from ftw.publisher.sender.workflows.interfaces import IWorkflowConfigs
from ftw.publisher.sender.workflows.interfaces import PUSH_ACTIONS
from zope.component import getUtility


_marker = '_publisher_event_already_handled'


def publish_after_transition(context, event):
    """ This event handler is executed after each transition and
    publishes the object with ftw.publisher on certain transitions.

    Also when retracting an object, the object will be published,
    since we should not delete anything unless it's delete from the
    sender instance too. This is necessary for preventing
    inconsistency, which could occur when deleting a folder which
    contains published objects on the reciever site.
    """

    # the event handler will be run multiple times, so we need to
    # remember which event we've already handled.
    if getattr(event, _marker, False):
        return
    else:
        setattr(event, _marker, True)

    if not event.transition:
        return

    if is_temporary(context):
        return

    config = getUtility(IWorkflowConfigs).get_config_for(context)
    if config is None:
        return

    transition = event.transition.__name__
    action = config.transitions().get(transition, None)

    if action is None:
        return

    if action in PUSH_ACTIONS:
        context.restrictedTraverse('@@publisher.publish')()
    elif action in DELETE_ACTIONS:
        context.restrictedTraverse('@@publisher.delete')()
