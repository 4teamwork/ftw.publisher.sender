from ftw.publisher.sender.interfaces import IQueue
from transaction import savepoint
from zope.annotation.interfaces import IAnnotations


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


def upgrade_executed_jobs_storage(portal_setup):
    """The executed jobs storage has changed from PersistentList
    to IOBTree storage, so we need to migrate the storage.

    """
    portal = portal_setup.portal_url.getPortalObject()
    queue = IQueue(portal)
    annotations = IAnnotations(portal)

    if 'publisher-executed' not in annotations:
        # No data to migrate.
        return

    # get jobs directly from the annotations - accessing with
    # queue methods is not possible yet
    jobs = list(annotations.get('publisher-executed', []))

    # drop the current list
    del annotations['publisher-executed']

    # add every single job with the new methods
    for job in jobs:
        queue.append_executed_job(job)

    # check if it worked
    assert len(jobs) == queue.get_executed_jobs_length()
