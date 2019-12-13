from collective.easyform.api import get_context
from ftw.publisher.sender.interfaces import IConfig
from ftw.publisher.sender.utils import sendRequestToRealm
from ftw.publisher.sender.workflows.interfaces import IPublisherContextState
from zope.component import getMultiAdapter
from zope.component.hooks import getSite
import os


def download(self, response):
    """This patch combines the data from the sender installation and the receiver
    installation to one csv / tsv.
    We assume that the form config is the same on both sides.

    The concept is to first execute the standard implementation, which sets the
    response headers and streams the local data.

    If the context is considered public, the second step is to get the data from
    the remote realms and append it to the response body (with response.write).

    This will combine the data of the all sites in a streamed http response.

    This implementation also works in local development with two plone sites,
    assuming that the receiver side does not have any realms configured.
    """

    self._old_download(response)

    site = getSite()
    realms = IConfig(site).getRealms()
    if not realms:
        return

    pub_state = getMultiAdapter((get_context(self), response), IPublisherContextState)
    if not pub_state.is_parent_published():
        return

    site_path = '/'.join(site.getPhysicalPath())
    context_path = '/'.join(get_context(self).getPhysicalPath())
    relative_path = os.path.relpath(context_path, site_path)
    view_path = '/'.join((relative_path, '@@actions', self.__name__, '@@data'))

    for realm in realms:
        remote_response = sendRequestToRealm(getSite().REQUEST.form.copy(),
                                             realm,
                                             view_path.lstrip('/'),
                                             return_response=True)

        if remote_response.code != 200:
            raise ValueError('Bad response from remote realm ({} {}): {!r}..'.format(
                remote_response.code,
                remote_response.msg,
                remote_response.read(100),
            ))

        try:
            response.write(remote_response.read())
        finally:
            remote_response.close()
