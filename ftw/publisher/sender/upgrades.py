from zope.annotation.interfaces import IAnnotations
from transaction import savepoint

def RemoveAnnotations(portal_setup):
    plone = portal_setup.portal_url.getPortalObject()
    
    annotations = IAnnotations(plone)
    del annotations['publisher-queue']
    del annotations['publisher-realms']
    savepoint(1)