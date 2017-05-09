from ftw.upgrade import UpgradeStep
from ftw.publisher.sender.hooks import add_saved_input_to_ignored_fields


class AddSavedDataToIgnoredFields(UpgradeStep):
    """Add saved data to ignored fields.
    """

    def __call__(self):
        add_saved_input_to_ignored_fields(self.portal)
