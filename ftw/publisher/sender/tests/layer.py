from Products.PloneTestCase import ptc
import collective.testcaselayer.ptc

ptc.setupPloneSite()

class IntegrationTestLayer(collective.testcaselayer.ptc.BasePTCLayer):

    def afterSetUp(self):
        # Install the opengever.document product
        self.addProfile('ftw.publisher.sender:default')
        #ptc.installPackage('PloneFormGen')
        #self.addProfile('Products.PloneFormGen:default')
        

Layer = IntegrationTestLayer([collective.testcaselayer.ptc.ptc_layer])