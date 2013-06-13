from ftw.upgrade import UpgradeStep


class InstallPermission(UpgradeStep):

    def __call__(self):
        self.setup_install_profile(
            'profile-ftw.publisher.sender.upgrades:2000')
