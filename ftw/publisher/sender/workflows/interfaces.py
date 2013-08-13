from zope.interface import Interface

PUBLISH = 'publish'
SUBMIT = 'submit'
RETRACT = 'retract'
DELETE = 'delete'

VALID_ACTIONS = (PUBLISH, SUBMIT, RETRACT, DELETE, None)
PUSH_ACTIONS = (PUBLISH, RETRACT)
DELETE_ACTIONS = (DELETE,)

PUBLISHED = 'published state'
REVISION = 'revision state'
VALID_STATES = (PUBLISHED, REVISION, None)


class IWorkflowConfigs(Interface):
    """A utility providing information for the publisher integration
    of the workflow.
    """

    def is_published(context):
        """Returns whether the passed context is considered published.
        """

    def is_in_revision(context):
        """Returns whether the passed context is considered in revision.
        """

    def get_config_for(context):
        """Returns the workflow config for the passed context.
        `None` is returned if the context has no workflow configured
        for publishing.
        """


class IWorkflowConfiguration(Interface):
    """The workflow configuration provides information about the meaning
    of states and transitions in a certain publisher aware workflow.

    The adapter, adapting the request, shall have the ID of the workflow.
    """

    def __init__(request):
        """The named adapter adapts the request.
        """

    def states():
        """Returns a dict where the key is the state ID and the value
        is the kind of status it is.

        The values should be constants from the
        ftw.publisher.sender.workflows.interfaces modules:

        PUBLISHED : contents in this state are published
        REVISION : contents in this state are in revision
        None : contents in this state are not published.
        """

    def transitions():
        """Returns a dict of transitions where the key is the transition
        ID and the value is the kind of transition it is.

        The values should be constants from the
        ftw.publisher.sender.workflows.interfaces modules:

        PUBLISH : this transition should publish the content
        SUBMIT : this transition does not publish the content but the checks
        for publishing are executed
        RETRACT : this transition retracts the content, which hides it from
        the other installation
        DELETE : this transition removes the content entirely from the other
        installation - this should usually not be used since it is recursive.
        """
