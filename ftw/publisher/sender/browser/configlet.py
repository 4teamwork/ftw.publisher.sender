#
# File:     communication.py
# Author:   Jonas Baumann <j.baumann@4teamwork.ch>
# Modified: 06.03.2009
#
# Copyright (c) 2007 by 4teamwork.ch
#
# GNU General Public License (GPL)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
__author__ = """Jonas Baumann <j.baumann@4teamwork.ch>"""

# python imports
import md5
from persistent.list import PersistentList

# Zope imports
from Products.Five import BrowserView
from z3c.form import form, field, button
from z3c.form import interfaces

# plone imports
from Products.statusmessages.interfaces import IStatusMessage
from plone.z3cform import z2

# publisher imports
from ftw.publisher.sender.persistence import Queue, Config, Realm
from ftw.publisher.sender.browser.interfaces import IRealmSchema, IEditRealmSchema
from ftw.publisher.sender.utils import sendRequestToRealm

# -- Forms

class CreateRealmForm(form.Form):
    """
    The CreateRealmForm is a z3c-form used for adding a new Realm
    instance to the publisher configuration.
    
    @cvar fields:           fields from the schema IRealmSchema
    @cvar ignoreContext:    do not use context (z3c-form setting)
    @cvar label:            label of the form
    """
    fields = field.Fields(IRealmSchema)
    ignoreContext = True
    label = u'Add Realm'

    @button.buttonAndHandler(u'Add Realm')
    def handleAdd(self, action):
        """
        This handler handles a click on the "Add Realm"-Button.
        If no errors occured, it adds a new Realm to the Config.
        @param action:      ActionInfo object provided by z3c.form
        @return:            None (form is shown) or Response-redirect
        """
        data, errors = self.extractData()
        config = Config(self.context)
        if len(errors)==0:
            # url + username has to be unique
            for realm in config.getRealms():
                if realm.url==data['url'] and realm.username==data['username']:
                    self.statusMessage(
                            'This URL / Username combination already exists!',
                            'error'
                    )
                    return
            kwargs = {
                'active' : data['active'] and 1 or 0,
                'url' : data['url'],
                'username' : data['username'],
                'password' : data['password'],
            }
            realm = Realm(**kwargs)
            config.appendRealm(realm)
            self.statusMessage('Added realm successfully')
            return self.request.RESPONSE.redirect('./@@publisher-config')

    def statusMessage(self, message, type='info'):
        """
        Adds a Plone statusMessage to the session.
        @param message:         Message to display
        @type message:          string
        @param type:            Type of the message [info|warning|error]
        @type type:             string
        @return:                None
        """
        IStatusMessage(self.request).addStatusMessage(
                message,
                type=type
        )


class EditRealmForm(form.EditForm):
    """
    The EditRealmForm is used for editing a Realm object.

    @cvar fields:           fields from the schema IRealmSchema
    @cvar ignoreContext:    do not use context (z3c-form setting)
    @cvar label:            label of the form
    """
    fields = field.Fields(IEditRealmSchema)
    ignoreContext = True
    label = u'Edit Realm'

    def updateWidgets(self):
        """
        Updates the widgets (z3c-form method).
        Customized for adding a HIDDEN_MODE-Flag to the ID-field.
        """
        super(EditRealmForm, self).updateWidgets()
        self.widgets['id'].mode = interfaces.HIDDEN_MODE

    @button.buttonAndHandler(u'Save Realm')
    def handleSave(self, action):
        """
        """
        data, errors = self.extractData()
        config = Config(self.context)
        if len(errors)==0:
            # get realm
            currentRealm = self.getRealmById(data['id'])
            if not currentRealm:
                raise Exception('Could not find realm')
            # no other realm should have same url+username
            for realm in config.getRealms():
                if realm!=currentRealm:
                    if realm.username==data['username'] and realm.url==data['url']:
                        self.statusMessage(
                                'This URL / Username combination already exists!',
                        )
                        return
            # update realm
            currentRealm.active = data['active'] and 1 or 0
            currentRealm.url = data['url']
            currentRealm.username = data['username']
            if data['password'] and len(data['password'])>0:
                currentRealm.password = data['password']
            self.statusMessage('Updated realm successfully')
            return self.request.RESPONSE.redirect('./@@publisher-config')

    def statusMessage(self, message, type='info'):
        IStatusMessage(self.request).addStatusMessage(
                message,
                type=type
        )

    def makeRealmId(self, realm):
        return md5.md5('%s-%s' % (realm.url, realm.username)).hexdigest()

    def getRealmById(self, id):
        for realm in Config(self.context).getRealms():
            if self.makeRealmId(realm)==id:
                return realm
        return None


# -- Views

class PublisherConfigletView(BrowserView):

    def __init__(self, *args, **kwargs):
        super(PublisherConfigletView, self).__init__(*args, **kwargs)
        self.config = Config(self.context)
        self.queue = Queue(self.context)

    def makeRealmId(self, realm):
        return md5.md5('%s-%s' % (realm.url, realm.username)).hexdigest()

    def getRealmById(self, id):
        for realm in self.config.getRealms():
            if self.makeRealmId(realm)==id:
                return realm
        return None

    def statusMessage(self, message, type='info'):
        IStatusMessage(self.request).addStatusMessage(
                message,
                type=type
        )
    

class ConfigView(PublisherConfigletView):

    def getQueueSize(self):
        return Queue(self.context).countJobs()

    def getRealms(self):
        """
        Returns a list of realms prepared for the template
        Example: [
            {
                'id' : '7815696ecbf1c96e6894b779456d330e',
                'active' : True,
                'url' : 'http://localhost:8080/targetSite/',
                'username' : 'blubb',
                'odd' : True,
            },
            {
                'id' : 'a67995ad3ec084cb38d32725fd73d9a3',
                'active' : False,
                'url' : 'http://localhost:8080/targetSite/',
                'username' : 'bla',
                'odd' : False,
            }
        ]
        """
        realmlist = []
        for i, realm in enumerate(self.config.getRealms()):
            id = self.makeRealmId(realm)
            realmlist.append({
                'id' : id,
                'active' : realm.active,
                'url' : realm.url,
                'username' : realm.username,
                'odd' : not ((i/2)*2==i),
            })
        return realmlist


class ListJobs(PublisherConfigletView):

    def getJobs(self):
        """
        Returns all jobs that are currently in the queue.
        """
        return self.queue.getJobs()


class CleanJobs(PublisherConfigletView):

    def __call__(self, *args, **kwargs):
        self.queue._setJobs(PersistentList())
        self.statusMessage('Removed all jobs from queue')
        return self.request.RESPONSE.redirect('./@@publisher-config')

class ExecuteJobs(PublisherConfigletView):
    
    def __call__(self, *args, **kwargs):
        self.output = self.context.restrictedTraverse('publisher.executeQueue')()
        self.output = self.output.replace('\n','<br/>')
        return super(ExecuteJobs, self).__call__(self, *args, **kwargs)


class AddRealm(PublisherConfigletView):

    def __call__(self, *args, **kwargs):
        self.form = self.renderForm()
        return super(AddRealm, self).__call__(*args, **kwargs)

    def renderForm(self):
        z2.switch_on(self)
        form = CreateRealmForm(self.context, self.request)
        return form()


class EditRealm(PublisherConfigletView):

    def __call__(self, *args, **kwargs):
        # set object values
        id = self.request.get('form.widgets.id', '')
        if id and isinstance(id, str):
            self.request.set('form.widgets.id', id.decode('utf8'))
        realm = self.getRealmById(id)
        if not realm:
            raise Exception('Could not find realm')
        values = realm.__dict__.copy()
        values['active'] = [unicode(bool(values['active'] and 1 or 0)).lower()]
        for k, v in values.items():
            key = 'form.widgets.%s' % k
            if key not in self.request.keys():
                if isinstance(v, str):
                    v = v.decode('utf8')
                self.request.set(key, v)
        self.form = self.renderForm()
        return super(PublisherConfigletView, self).__call__(*args, **kwargs)

    def renderForm(self):
        z2.switch_on(self)
        form = EditRealmForm(self.context, self.request)
        return form()


class DeleteRealm(PublisherConfigletView):

    def __call__(self, *args, **kwargs):
        id = self.context.request.get('id', '')
        realm = self.getRealmById(id)
        if not realm:
            self.statusMessage('Could not find realm', 'error')
        else:
            self.config.removeRealm(realm)
            self.statusMessage('Removed realm')
        return self.request.RESPONSE.redirect('./@@publisher-config')

class TestRealm(PublisherConfigletView):

    def __call__(self, *args, **kwargs):
        id = self.context.request.get('id', '')
        realm = self.getRealmById(id)
        if not realm:
            self.statusMessage('Could not find realm', 'error')
        else:
            responseText = sendRequestToRealm({}, realm, 'publisher.testConnection')
            if responseText=='ok':
                self.statusMessage('Connection okay')
            else:
                self.statusMessage(
                        'Connection failed: %s' % responseText,
                        'error'
                )
        return self.request.RESPONSE.redirect('./@@publisher-config')

