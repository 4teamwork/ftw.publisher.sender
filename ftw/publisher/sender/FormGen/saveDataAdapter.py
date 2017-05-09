from ftw.publisher.sender import _
from ftw.publisher.sender.utils import sendRequestToRealm
from ftw.publisher.sender.interfaces import IConfig
from ftw.publisher.sender.workflows.interfaces import IPublisherContextState
from Products.statusmessages.interfaces import IStatusMessage
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility
from Acquisition import aq_parent
from Products.Archetypes.utils import contentDispositionHeader
from zope.component import getMultiAdapter


def download(self, REQUEST=None, RESPONSE=None):
    """Download the saved data
    """
    url_tool = getToolByName(self, 'portal_url')
    config = IConfig(url_tool.getPortalObject())
    pub_state = getMultiAdapter((self, REQUEST), IPublisherContextState)
    realms = config.getRealms()
    download_format = getattr(self, 'DownloadFormat', 'csv')

    if len(realms) == 0 or not pub_state.is_parent_published():
        if download_format == 'tsv':
            return self.download_tsv(REQUEST, RESPONSE)
        else:
            assert download_format == 'csv', 'Unknown download format'
            return self.download_csv(REQUEST, RESPONSE)

    elif len(realms) == 1:
        data = {'uid': self.UID(), 'download_format': download_format}
        return_data = sendRequestToRealm(data,
                                         realms[0],
                                         'formgen_get_saved_data')
        filename = self.id
        if filename.find('.') < 0:
            filename = '%s.%s' % (filename, download_format)
        header_value = contentDispositionHeader('attachment',
                                                self.getCharset(),
                                                filename=filename)
        RESPONSE.setHeader("Content-Disposition", header_value)
        sep_type = download_format == 'csv' and 'comma' or 'tab'
        RESPONSE.setHeader("Content-Type",
                           'text/%s-separated-values;'
                           'charset=%s' % (sep_type, self.getCharset()))
        return return_data

    else:
        messages = IStatusMessage(self.request)
        messages.add(_(u"couldn't determine correct realm to fetch from."),
                     type=u"error")
        return RESPONSE.redirect(self.context.absolute_url())

