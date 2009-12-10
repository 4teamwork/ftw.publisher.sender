from zope.annotation.interfaces import IAnnotations
from transaction import savepoint

def RemoveAnnotations(portal_setup):
    plone = portal_setup.portal_url.getPortalObject()
    
    annotations = IAnnotations(plone)
    if annotations.has_key('publisher-queue'):
        del annotations['publisher-queue']
    if annotations.has_key('publisher-realms'):
        del annotations['publisher-realms']
    if annotations.has_key('publisher-dataFolder'):
        del annotations['publisher-dataFolder']
    
    savepoint(1)
