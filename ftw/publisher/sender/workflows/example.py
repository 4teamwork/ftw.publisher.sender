from ftw.publisher.sender.workflows import interfaces
from ftw.publisher.sender.workflows.config import LawgiverWorkflowConfiguration


class ExampleWorkflowConfiguration(LawgiverWorkflowConfiguration):
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
