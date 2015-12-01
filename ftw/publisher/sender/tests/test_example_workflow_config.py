from ftw.publisher.sender.testing import PUBLISHER_SENDER_INTEGRATION_TESTING
from ftw.publisher.sender.tests.base import WorkflowConfigTest


class TestWorkflowConfig(WorkflowConfigTest):

    layer = PUBLISHER_SENDER_INTEGRATION_TESTING
    workflow_id = 'publisher-example-workflow'
