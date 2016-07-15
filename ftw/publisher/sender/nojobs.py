from contextlib import contextmanager
from zope.globalrequest import getRequest
from zope.interface import alsoProvides
from zope.interface import Interface
from zope.interface import noLongerProvides


class IPublisherJobsDisabled(Interface):
    """Request marker interface for when no
    publisher jobs should be added.
    """


@contextmanager
def publisher_jobs_disabled():
    """Do not add publisher jobs within this context manager.
    """
    request = getRequest()
    if not request:
        raise ValueError('Cannot disable publisher jobs:'
                         ' there is no global request.')

    alsoProvides(request, IPublisherJobsDisabled)
    try:
        yield
    finally:
        noLongerProvides(request, IPublisherJobsDisabled)


def publisher_jobs_are_disabled():
    request = getRequest()
    if not request:
        return False
    return IPublisherJobsDisabled.providedBy(request)
