from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from ftw.publisher.sender import message_factory as _
from ftw.publisher.sender.browser.interfaces import IBlacklistPathSchema
from ftw.publisher.sender.interfaces import IConfig
from ftw.table.interfaces import ITableGenerator
from plone.z3cform import z2
from plone.z3cform.interfaces import IWrappedForm
from z3c.form import button
from z3c.form import field
from z3c.form import form
from zope.component import getUtility
from zope.interface import implements


class AddPathForm(form.Form):
    implements(IWrappedForm)

    fields = field.Fields(IBlacklistPathSchema)
    ignoreContext = True
    label = _(u'form_label_add_path',
              default=u'Add path')

    @button.buttonAndHandler(_(u'button_add_path',
                               default=u'Add path'))
    def handleAdd(self, action):
        portal = self.context.portal_url.getPortalObject()
        config = IConfig(portal)
        data, errors = self.extractData()
        if not len(errors):
            path = data.get('path').strip()
            if not path.startswith('/'):
                raise Exception('Path does not start with /')
            config.appendPathToBlacklist(path)
            message = _(u'info_path_added',
                        default=u'Path added')
            IStatusMessage(self.request).addStatusMessage(
                message, type='info')
            return self.request.RESPONSE.redirect('./@@publisher-config-blacklist')


class PathBlacklistView(BrowserView):

    def __init__(self, *args, **kwargs):
        super(PathBlacklistView, self).__init__(*args, **kwargs)
        self.portal = self.context.portal_url.getPortalObject()
        self.config = IConfig(self.portal)

    def __call__(self, *args, **kwargs):
        delete = self.request.get('delete', None)
        if delete:
            if self.config.removePathFromBlacklist(delete):
                msg = _(u'info_path_removed',
                        default=u'Removed path ${path} from blacklist',
                        mapping={'path': delete})
                IStatusMessage(self.request).addStatusMessage(msg, type='info')
            return self.request.RESPONSE.redirect('./@@publisher-config-blacklist')
        return super(PathBlacklistView, self).__call__(*args, **kwargs)

    def render_table(self):
        generator = getUtility(ITableGenerator, 'ftw.tablegenerator')
        return generator.generate(self._table_rows(), self._table_columns())

    def render_add_form(self):
        z2.switch_on(self)
        form = AddPathForm(self.context, self.request)
        return form()

    def _table_rows(self):
        for path in self.config.getPathBlacklist():
            yield {
                'Path': path,
                '': '<a href="./@@publisher-config-blacklist?delete=%s">Delete</a>' % \
                    path,
                }

    def _table_columns(self):
        return ('Path', '')
