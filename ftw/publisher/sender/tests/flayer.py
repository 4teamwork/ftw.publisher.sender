from collective.testcaselayer import ptc as tcl_ptc
from collective.testcaselayer import common

class Layer(tcl_ptc.BasePTCLayer):
    """Install ftw.publisher.sender"""

    def afterSetUp(self):
        self.addProfile('ftw.publisher.sender:default')

layer = Layer([common.common_layer])
