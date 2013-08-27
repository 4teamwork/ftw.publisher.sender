from ftw.publisher.sender import _
from ftw.publisher.sender.workflows import config
from ftw.publisher.sender.workflows import constraints
from ftw.publisher.sender.workflows import interfaces
from ftw.publisher.sender.workflows.constraints import error_on
from ftw.publisher.sender.workflows.constraints import message
from ftw.publisher.sender.workflows.constraints import warning_on


class ExampleWorkflowConfiguration(config.LawgiverWorkflowConfiguration):
    workflow_id = 'publisher-example-workflow'

    def lawgiver_states(self):
        return {
            'Internal': None,
            'Pending': None,
            'Published': interfaces.PUBLISHED,
            'Revision': interfaces.REVISION}

    def lawgiver_transitions(self):
        return {
            'submit (Internal => Pending)': interfaces.SUBMIT,
            'publish (Internal => Published)': interfaces.PUBLISH,
            'reject (Pending => Internal)': None,
            'publish (Pending => Published)': interfaces.PUBLISH,
            'retract (Published => Internal)': interfaces.RETRACT,
            'revise (Published => Revision)': None,
            'publish (Revision => Published)': interfaces.PUBLISH,
            }


class ExampleWorkflowConstraintDefinition(constraints.ConstraintDefinition):

    @message(_('The parent object needs to be published first.'))
    @error_on(interfaces.PUBLISH)
    @warning_on(interfaces.SUBMIT)
    def parent_needs_to_be_published(self):
        return self.state().is_parent_published()
    # return self.state().is_parent_published() or self.state().is_in_revision()

    @message(_('The child object ${item} is still published.'))
    @warning_on(interfaces.RETRACT)
    def retract_children_first(self):
        return list(self.state().get_published_children())

    @message(_('The referenced object ${item} is not yet published.'))
    @warning_on(interfaces.PUBLISH, interfaces.SUBMIT)
    def references_should_be_published(self):
        return list(self.state().get_unpublished_references())

    @message(_('The referenced object ${item} is still published.'))
    @warning_on(interfaces.DELETE, interfaces.RETRACT)
    def references_may_be_retracted_too(self):
        return list(self.state().get_published_references())
