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
import datetime

# Zope imports
from Products.Five import BrowserView
from z3c.form import form, field, button
from z3c.form import interfaces
from zope.component import getUtility

# plone imports
from Products.statusmessages.interfaces import IStatusMessage
from plone.z3cform import z2
from ftw.table.interfaces import ITableGenerator

# publisher imports
from ftw.publisher.sender.persistence import Realm
from ftw.publisher.sender.interfaces import IQueue, IConfig
from ftw.publisher.sender.browser.interfaces import IRealmSchema, IEditRealmSchema
from ftw.publisher.sender.utils import sendRequestToRealm
from ftw.publisher.core import states

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
        config = IConfig(self.context)
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
        config = IConfig(self.context)
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
        for realm in IConfig(self.context).getRealms():
            if self.makeRealmId(realm)==id:
                return realm
        return None


# -- Views

class PublisherConfigletView(BrowserView):

    def __init__(self, *args, **kwargs):
        super(PublisherConfigletView, self).__init__(*args, **kwargs)
        self.config = IConfig(self.context)
        self.queue = IQueue(self.context)

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

    def __call__(self, *args, **kwargs):
        redirect = False
        if self.request.get('enable-publishing'):
            self.config.set_publishing_enabled(True)
            redirect = True
        elif self.request.get('disable-publishing'):
            self.config.set_publishing_enabled(False)
            redirect = True

        if redirect:
            return self.request.RESPONSE.redirect('./@@publisher-config')
        return super(ConfigView, self).__call__(*args, **kwargs)

    def getQueueSize(self):
        return IQueue(self.context).countJobs()

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

    def get_cache_folder_path(self):
        return self.config.getDataFolder()


class ListJobs(PublisherConfigletView):

    def getJobs(self):
        """
        Returns all jobs that are currently in the queue.
        """
        return self.queue.getJobs()


class ListExecutedJobs(PublisherConfigletView):

    def __call__(self, *args, **kwargs):
        redirect = False
        if self.request.get('button.cleanup'):
            for job in self.queue.get_executed_jobs()[:]:
                self.queue.remove_executed_job(job)
                job.removeJob()
            redirect = True

        if self.request.get('button.delete.successfuls'):
            for job in self.queue.get_executed_jobs():
                state = job.get_latest_executed_entry()
                if isinstance(state, states.SuccessState):
                    self.queue.remove_executed_job(job)
                    job.removeJob()
                redirect = True

        if self.request.get('button.delete.olderthan'):
            days = int(self.request.get('days'))
            delta = datetime.timedelta(days)
            now = datetime.datetime.now()
            for job in self.queue.get_executed_jobs():
                if getattr(job, 'executed_list', None) == None:
                    continue
                xdate = job.executed_list[-1]['date']
                if xdate + delta < now:
                    self.queue.remove_executed_job(job)
                    job.removeJob()
            redirect = True

        deleteJob = self.request.get('delete.job')
        if deleteJob:
            for job in self.queue.get_executed_jobs():
                if job.get_filename() == deleteJob:
                    self.queue.remove_executed_job(job)
                    job.removeJob()
                    redirect = True
                    break

        requeueJob = self.request.get('requeue.job')
        if requeueJob:
            for job in self.queue.get_executed_jobs():
                if job.get_filename() == requeueJob:
                    self.queue.remove_executed_job(job)
                    job.move_jsonfile_to(self.config.getDataFolder())
                    self.queue.appendJob(job)
                    redirect = True
                    break

        if redirect:
            url = './@@publisher-config-listExecutedJobs'
            return self.request.RESPONSE.redirect(url)

        return super(ListExecutedJobs, self).__call__(*args, **kwargs)

    def render_table(self):
        generator = getUtility(ITableGenerator, 'ftw.tablegenerator')
        columns = ('Date', 'Title', 'Action', 'State', 'Username', '')
        return generator.generate(self._get_data(), columns)

    def _get_data(self):
        jobs = list(self.queue.get_executed_jobs())
        jobs.reverse()
        for job in jobs:
            state = job.get_latest_executed_entry()
            state_name = getattr(state, 'localized_name', None)
            if state_name:
                state_name = self.context.translate(state_name)
            else:
                state_name = state.__class__.__name__
            if isinstance(state, states.ErrorState):
                colored_state = '<span class="error" style="color:red;">' +\
                    '%s</span>' % self.context.translate(state_name)
            else:
                colored_state = '<span class="success">%s</span>' % state_name
            date = 'unknown'
            try:
                date = job.executed_list[-1]['date'].strftime('%d.%m.%Y %H:%M')
            except:
                pass
            ctrl = ' '.join((
                    '<a href="./@@publisher-config-executed-job-details' +\
                        '?job=%s">Details</a>' % job.get_filename(),
                    '<a href="./@@publisher-config-listExecutedJobs' +\
                        '?requeue.job=%s">Queue</a>' % job.get_filename(),
                    '<a href="./@@publisher-config-listExecutedJobs' +\
                        '?delete.job=%s">Delete</a>' % job.get_filename(),
                    ))
            shortened_title = job.objectTitle
            maximum_length = 35
            if len(shortened_title) > maximum_length:
                try:
                   shortened_title = shortened_title.decode('utf8')
                   shortened_title = shortened_title[:maximum_length] + u' ...'
                   shortened_title = shortened_title.encode('utf8')
                except:
                    pass
            yield {
                'Date': date,
                'Title': '<a href="%s" title="%s">%s</a>' % (
                    job.objectPath + '/view',
                    job.objectTitle,
                    shortened_title),
                'Action': job.action,
                'State': colored_state,
                'Username': job.username,
                '': ctrl,
                }


class ExecutedJobDetails(PublisherConfigletView):

    def __call__(self, *args, **kwargs):
        redirect_to = None

        if self.request.get('button.requeue'):
            job = self.get_job()
            self.queue.remove_executed_job(job)
            job.move_jsonfile_to(self.config.getDataFolder())
            self.queue.appendJob(job)
            redirect_to = './@@publisher-config'

        if self.request.get('button.delete'):
            job = self.get_job()
            self.queue.remove_executed_job(job)
            if job.json_file_exists():
                job.removeJob()
            redirect_to = './@@publisher-config-listExecutedJobs'

        if self.request.get('button.execute'):
            job = self.get_job()
            if job.json_file_exists():
                portal = self.context.portal_url.getPortalObject()
                execview = portal.restrictedTraverse('@@publisher.executeQueue')
                execview.execute_single_job(job)
            redirect_to = './@@publisher-config-executed-job-details?job=' + \
                job.get_filename()

        if redirect_to:
            return self.request.RESPONSE.redirect(redirect_to)

        return super(ExecutedJobDetails, self).__call__(*args, **kwargs)

    def get_job(self):
        job_filename = self.request.get('job')
        for job in self.queue.get_executed_jobs():
            if job.get_filename() == job_filename:
                return job

    def get_translated_state_name(self, state):
        name = getattr(state, 'localized_name', None)
        if name:
            return self.context.translate(name)
        else:
            return state.__class__.__name__


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


class ExecuteJob(PublisherConfigletView):

    def __call__(self, *args, **kwargs):
        job = self.get_job()
        if not job:
            raise Exception('No job found')
        portal = self.context.portal_url.getPortalObject()
        execview = portal.restrictedTraverse('@@publisher.executeQueue')
        execview.execute_single_job(job)
        redirect_to = './@@publisher-config-executed-job-details?job=' + \
            job.get_filename()
        return self.request.RESPONSE.redirect(redirect_to)

    def get_job(self):
        job_filename = self.request.get('job')
        for job in self.queue.getJobs():
            if job.get_filename() == job_filename:
                return job


class RemoveJob(PublisherConfigletView):

    def __call__(self, *args, **kwargs):
        job = self.get_job()
        if not job:
            raise Exception('No job found')
        self.queue.removeJob(job)
        job.removeJob()
        redirect_to = './@@publisher-config-listJobs'
        return self.request.RESPONSE.redirect(redirect_to)

    def get_job(self):
        job_filename = self.request.get('job')
        for job in self.queue.getJobs():
            if job.get_filename() == job_filename:
                return job


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

