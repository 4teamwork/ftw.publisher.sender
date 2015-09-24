from Acquisition import aq_inner
from Acquisition import aq_parent
from ftw.publisher.sender.utils import is_temporary
from ftw.publisher.sender.workflows.interfaces import DELETE_ACTIONS
from ftw.publisher.sender.workflows.interfaces import IPublisherContextState
from ftw.publisher.sender.workflows.interfaces import IWorkflowConfigs
from ftw.publisher.sender.workflows.interfaces import PUSH_ACTIONS
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zope.component import getMultiAdapter
from zope.component import getUtility
import pkg_resources


try:
    pkg_resources.get_distribution('ftw.simplelayout')
except pkg_resources.DistributionNotFound:
    FTW_SIMPLELAYOUT_AVAILABLE = False
else:
    FTW_SIMPLELAYOUT_AVAILABLE = True
    from ftw.publisher.core.adapters.ftw_simplelayout import is_sl_contentish


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



def handle_remove_event(context, event):
    """
    Before a object is remvoed the event handler crates a remove job.
    """

    # the event is notified for every subobject, but we only want to check
    # the top object which the users tries to delete
    if context is not event.object:
        return

    if FTW_SIMPLELAYOUT_AVAILABLE and is_sl_contentish(context):
        # Do not delete sl contentish objects, they are deleted when the
        # associated sl container is published.
        return

    # Find the workflow object by walking up. We may be deleting a file
    # within a file-block within a page, where file and file-block have no
    # workflow and we check the page workflow.
    obj = context
    state = None

    while not IPloneSiteRoot.providedBy(obj):
        state = getMultiAdapter((obj, context.REQUEST),
                                IPublisherContextState)
        if state.has_workflow():
            break
        else:
            obj = aq_parent(aq_inner(obj))

    if not state.has_workflow() or not state.has_publisher_config():
        # plone site reached without finding a workflow, therefore
        # the object was never published.
        return

    context.restrictedTraverse('@@publisher.delete')(no_response=True)
