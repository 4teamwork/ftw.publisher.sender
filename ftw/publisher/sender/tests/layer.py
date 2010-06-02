from Products.PloneTestCase import ptc
import collective.testcaselayer.ptc
from Testing import ZopeTestCase



import Products.PloneFormGen

ptc.setupPloneSite()

class IntegrationTestLayer(collective.testcaselayer.ptc.BasePTCLayer):

    def afterSetUp(self):
        self.addProfile('ftw.publisher.sender:default')
        
        self.addProfile('Products.PloneFormGen:default')
        

Layer = IntegrationTestLayer([collective.testcaselayer.ptc.ptc_layer])