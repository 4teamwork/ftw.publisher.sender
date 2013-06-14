from ftw.upgrade import UpgradeStep


class UpdateControlPanelAction(UpgradeStep):

    def __call__(self):
        self.setup_install_profile(
            'profile-ftw.publisher.sender.upgrades:2001')
