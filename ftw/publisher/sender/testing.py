from ftw.testing import ComponentRegistryLayer


class ZCMLLayer(ComponentRegistryLayer):

    def setUp(self):
        super(ZCMLLayer, self).setUp()

        import ftw.publisher.sender.tests
        self.load_zcml_file('tests.zcml', ftw.publisher.sender.tests)


ZCML_LAYER = ZCMLLayer()
