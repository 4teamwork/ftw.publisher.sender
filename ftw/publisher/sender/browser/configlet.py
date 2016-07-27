from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.PloneBatch import Batch
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from ZODB.POSException import ConflictError
from ftw.publisher.core import states
from ftw.publisher.sender import message_factory as _
from ftw.publisher.sender.browser.interfaces import IEditRealmSchema
from ftw.publisher.sender.browser.interfaces import IRealmSchema
from ftw.publisher.sender.interfaces import IConfig
from ftw.publisher.sender.interfaces import IQueue
from ftw.publisher.sender.persistence import Realm
from ftw.publisher.sender.utils import sendRequestToRealm
from ftw.table.interfaces import ITableGenerator
from persistent.dict import PersistentDict
from persistent.list import PersistentList
from plone.z3cform import z2
from plone.z3cform.interfaces import IWrappedForm
from z3c.form import button
from z3c.form import field
from z3c.form import form
from z3c.form import interfaces
from zope.component import getUtility
from zope.interface import implements
from zope.publisher.interfaces import Retry
import datetime
import md5


EXECUTED_JOBS_BATCH_SIZE = 100


# lets translate the actions with i18ndude
TRANSLATED_ACTIONS = {
    'push': _(u'action_push', default=u'Push'),
    'move': _(u'action_move', default=u'Move'),
    'delete': _(u'action_delete', default=u'Delete'),
    }


# -- Forms

class CreateRealmForm(form.Form):
    """
    The CreateRealmForm is a z3c-form used for adding a new Realm
    instance to the publisher configuration.

    @cvar fields:           fields from the schema IRealmSchema
    @cvar ignoreContext:    do not use context (z3c-form setting)
    @cvar label:            label of the form
    """
    implements(IWrappedForm)

    fields = field.Fields(IRealmSchema)
    ignoreContext = True
    label = u'Add Realm'

    @button.buttonAndHandler(_(u'button_save_realm', default=u'Save Realm'))
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
            assert config.is_update_realms_possible()
            # url + username has to be unique
            for realm in config.getRealms():
                if realm.url==data['url'] and realm.username==data['username']:
                    self.statusMessage(
                        'This URL / Username combination already exists!',
                        'error')
                    return
            kwargs = {
                'active': data['active'] and 1 or 0,
                'url': data['url'],
                'username': data['username'],
                'password': data['password'],
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
            type=type)


class EditRealmForm(form.EditForm):
    """
    The EditRealmForm is used for editing a Realm object.

    @cvar fields:           fields from the schema IRealmSchema
    @cvar ignoreContext:    do not use context (z3c-form setting)
    @cvar label:            label of the form
    """
    implements(IWrappedForm)

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

    @button.buttonAndHandler(_(u'button_save_realm', default=u'Save Realm'))
    def handleSave(self, action):
        """
        """
        data, errors = self.extractData()
        config = IConfig(self.context)
        assert config.is_update_realms_possible()
        if len(errors)==0:
            # get realm
            currentRealm = self.getRealmById(data['id'])
            if not currentRealm:
                raise Exception('Could not find realm')
            # no other realm should have same url+username
            for realm in config.getRealms():
                if realm!=currentRealm:
                    if realm.username==data['username'] and\
                       realm.url==data['url']:
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
            type=type)

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
            type=type)


class ConfigView(PublisherConfigletView):

    def __call__(self, *args, **kwargs):
        redirect = False
        if self.request.get('enable-publishing'):
            self.config.set_publishing_enabled(True)
            redirect = True
        elif self.request.get('disable-publishing'):
            self.config.set_publishing_enabled(False)
            redirect = True
        elif self.request.get('submit_ignored_fields'):
            ignore = {}
            add_ignore_id = self.request.get('add_ignore_id', None)
            add_ignore_fields = self.request.get('add_ignore_fields', None)
            #override saved ignores
            for ign_id in self.request.get('ign_ids', []):
                ign = self.request.get(ign_id, '')
                if ign.replace('\r\n', '').strip():
                    ignore[ign_id] = PersistentList(
                        [term.strip() for term in ign.split('\r\n') if term])
            # add new ignores
            if add_ignore_id and add_ignore_fields:
                fields = add_ignore_fields.split('\r\n')
                ignore[add_ignore_id] = PersistentList(
                    [term.strip() for term in fields if term])

            self.config.set_ignored_fields(PersistentDict(ignore))
            redirect = True

        #set locking flag
        if 'enable-locking' in self.request:
            self.config.set_locking_enabled(self.request.get('enable-locking'))
            redirect = True


        if redirect:
            return self.request.RESPONSE.redirect('./@@publisher-config')
        return super(ConfigView, self).__call__(*args, **kwargs)

    def getTypesInformation(self):
        """ Gets the ignored types form annotations.
            Returns the types with ignored fields and in second position
            all other types.
        """
        types_tool = getToolByName(self.context, 'portal_types')
        portal_types = types_tool.listTypeInfo()
        ignored_types = self.config.get_ignored_fields()
        portal_types = [ptype for ptype in portal_types \
                              if ptype.id not in ignored_types.keys()]
        return [ignored_types, portal_types]

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
                    'id': id,
                    'active': realm.active,
                    'url': realm.url,
                    'username': realm.username,
                    'odd': not ((i/2)*2==i),
                    })
        return realmlist

    def get_cache_folder_path(self):
        return self.config.getDataFolder()

    def get_clear_confirm_message(self):
        """Translated confirm message for clearing the queue
        """
        return self.context.translate(_(
                u'confirm_clear_queue',
                default=u'Are you sure to delete all jobs in the queue?'))


class ListJobs(PublisherConfigletView):

    def getJobs(self):
        """
        Returns all jobs that are currently in the queue.
        """
        return self.queue.getJobs()


class ListExecutedJobs(PublisherConfigletView):

    COLUMNS = (('date', _(u'th_date', default=u'Date')),
               ('title', _(u'th_title', default=u'Title')),
               ('action', _(u'th_action', default=u'Action')),
               ('state', _(u'th_state', default=u'State')),
               ('username', _(u'th_username', default=u'Username')),
               ('', ''))

    def __call__(self, *args, **kwargs):

        redirect = False
        if self.request.get('button.cleanup'):
            self.queue.clear_executed_jobs()
            redirect = True

        if self.request.get('button.delete.olderthan'):
            days = int(self.request.get('days'))
            date = datetime.datetime.now() - datetime.timedelta(days)
            self.queue.remove_executed_jobs_older_than(date)
            redirect = True

        requeueJob = self.request.get('requeue.job')
        if requeueJob:
            key = int(requeueJob)
            try:
                job = self.queue.get_executed_job_by_key(key)
            except KeyError:
                # could not find job
                pass
            else:
                self.queue.remove_executed_job(key)
                job.move_jsonfile_to(self.config.getDataFolder())
                self.queue.appendJob(job)
                redirect = True

        if redirect:
            url = './@@publisher-config-listExecutedJobs'
            return self.request.RESPONSE.redirect(url)

        # BATCH
        # create a fake iterable object with the length of all objects,
        # but we dont want to load them all..
        fake_data = xrange(self.queue.get_executed_jobs_length())
        b_start = int(self.request.get('b_start', 0))
        self.batch = Batch(fake_data, EXECUTED_JOBS_BATCH_SIZE, b_start)

        return super(ListExecutedJobs, self).__call__(*args, **kwargs)

    def render_table(self):
        generator = getUtility(ITableGenerator, 'ftw.tablegenerator')
        columns = [c[1] for c in ListExecutedJobs.COLUMNS]
        return generator.generate(self._get_data(), columns)

    def _get_data(self):
        columns = dict(ListExecutedJobs.COLUMNS)
        i18n_details = self.context.translate(_(
                u'link_job_details',
                default=u'Details'))
        i18n_requeu = self.context.translate(_(
                u'link_requeue_job',
                default='Requeue'))
        # get a batched part of the executed jobs. But we need to start
        # batching at the end, get the batch forward and then reverse,
        # because we want the newest job at the top.
        b_start = int(self.request.get('b_start', 0))
        jobs_length = self.queue.get_executed_jobs_length()
        end = jobs_length - b_start
        start = end - EXECUTED_JOBS_BATCH_SIZE
        if start < 0:
            start = 0
        entries = list(self.queue.get_executed_jobs(start, end))
        entries.reverse()
        for key, job in entries:
            state = job.get_latest_executed_entry()
            state_name = getattr(state, 'localized_name', None)
            if state_name:
                state_name = self.context.translate(state_name)
            else:
                state_name = state.__class__.__name__
            if isinstance(state, states.ErrorState):
                colored_state = '<span class="error" style="color:red;">' +\
                    '%s</span>' % self.context.translate(state_name)
            elif isinstance(state, states.WarningState):
                colored_state = '<span class="error" style="color:orange;">' +\
                    '%s</span>' % self.context.translate(state_name)
            else:
                colored_state = '<span class="success">%s</span>' % state_name
            date = 'unknown'
            try:
                date = job.executed_list[-1]['date'].strftime('%d.%m.%Y %H:%M')
            except (ConflictError, Retry):
                raise
            except:
                pass
            ctrl = ' '.join((
                    '<a href="./@@publisher-config-executed-job-details' +\
                        '?job=%s">%s</a>' % (key, i18n_details),
                    '|',
                    '<a href="./@@publisher-config-listExecutedJobs' +\
                        '?requeue.job=%s">%s</a>' % (key, i18n_requeu),
                    ))
            shortened_title = job.objectTitle
            maximum_length = 35

            if len(shortened_title) > maximum_length:
                try:
                    shortened_title = shortened_title.decode('utf8')
                    shortened_title = shortened_title[:maximum_length] + \
                                      u' ...'
                    shortened_title = shortened_title.encode('utf8')
                except (ConflictError, Retry):
                    raise
                except:
                    pass
            yield {
                columns['date']: date,
                columns['title']: '<a href="%s" title="%s">%s</a>' % (
                    job.objectPath + '/view',
                    job.objectTitle,
                    shortened_title),
                columns['action']: TRANSLATED_ACTIONS.get(job.action,
                                                          job.action),
                columns['state']: colored_state,
                columns['username']: job.username,
                columns['']: ctrl,
                }

    def get_translated_cleanup_prompt(self):
        """Returns the converted prompt string which is displayed when
        clicking on "cleanup".

        """
        return self.context.translate(_(
                u'prompt_cleanup',
                default=u'Are you shure to delete all executed jobs?'))


class ExecutedJobDetails(PublisherConfigletView):

    def __call__(self, *args, **kwargs):
        redirect_to = None

        self.key = int(self.request.get('job'))
        self.job = self.queue.get_executed_job_by_key(self.key)

        if self.request.get('button.requeue'):
            if self.job.json_file_exists():
                self.queue.remove_executed_job(self.key)
                self.job.move_jsonfile_to(self.config.getDataFolder())
                self.queue.appendJob(self.job)
                msg = _(u'info_requeued_job',
                        default=u'The job has been moved to the queue.')
                IStatusMessage(self.request).addStatusMessage(msg,
                                                              type='info')
                redirect_to = './@@publisher-config'
            else:
                msg = _(u'error_job_data_file_missing',
                        default=u'The data file of the job is missing.')
                IStatusMessage(self.request).addStatusMessage(msg,
                                                              type='error')

        if self.request.get('button.delete'):
            self.queue.remove_executed_job(self.key)
            if self.job.json_file_exists():
                self.job.removeJob()
            msg = _(u'info_job_deleted',
                    default=u'The job has been deleted.')
            IStatusMessage(self.request).addStatusMessage(msg,
                                                          type='info')
            redirect_to = './@@publisher-config-listExecutedJobs'

        if self.request.get('button.execute'):
            if self.job.json_file_exists():
                portal = self.context.portal_url.getPortalObject()
                execview = portal.restrictedTraverse(
                    '@@publisher.executeQueue')
                execview.execute_single_job(self.job)
                msg = _(u'info_job_executed',
                        default=u'The job has been executed.')
                IStatusMessage(self.request).addStatusMessage(msg,
                                                              type='info')
            else:
                msg = _(u'error_job_data_file_missing',
                        default=u'The data file of the job is missing.')
                IStatusMessage(self.request).addStatusMessage(msg,
                                                              type='error')
            redirect_to = './@@publisher-config-executed-job-details?job=' + \
                str(self.key)

        if redirect_to:
            return self.request.RESPONSE.redirect(redirect_to)

        return super(ExecutedJobDetails, self).__call__(*args, **kwargs)

    def get_translated_state_name(self, state):
        name = getattr(state, 'localized_name', None)
        if name:
            return self.context.translate(name)
        else:
            return state.__class__.__name__

    def get_translated_action(self):
        return TRANSLATED_ACTIONS.get(self.job.action, self.job.action)


class CleanJobs(PublisherConfigletView):

    def __call__(self, *args, **kwargs):
        self.queue.clearJobs()
        self.statusMessage('Removed all jobs from queue')
        return self.request.RESPONSE.redirect('./@@publisher-config')


class ExecuteJobs(PublisherConfigletView):

    def __call__(self, *args, **kwargs):
        self.output = self.context.restrictedTraverse(
            'publisher.executeQueue')()
        self.output = self.output.replace('\n', '<br/>')
        return super(ExecuteJobs, self).__call__(self, *args, **kwargs)


class ExecuteJob(PublisherConfigletView):

    def __call__(self, *args, **kwargs):
        job = self.get_job()
        if not job:
            raise Exception('No job found')
        portal = self.context.portal_url.getPortalObject()
        execview = portal.restrictedTraverse('@@publisher.executeQueue')
        key = execview.execute_single_job(job)
        redirect_to = './@@publisher-config-executed-job-details?job=' + \
            str(key)
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
        assert self.config.is_update_realms_possible()
        self.form = self.renderForm()
        return super(AddRealm, self).__call__(*args, **kwargs)

    def renderForm(self):
        z2.switch_on(self)
        form = CreateRealmForm(self.context, self.request)
        return form()


class EditRealm(PublisherConfigletView):

    def __call__(self, *args, **kwargs):
        assert self.config.is_update_realms_possible()
        # set object values
        id = self.request.get('form.widgets.id', '')
        if id and isinstance(id, str):
            self.request.set('form.widgets.id', id.decode('utf8'))
        realm = self.getRealmById(id)
        if not realm:
            raise Exception('Could not find realm')
        values = realm.__dict__.copy()
        values['active'] = values['active'] and ['selected'] or []

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
        assert self.config.is_update_realms_possible()
        id = self.request.get('id', '')
        realm = self.getRealmById(id)
        if not realm:
            self.statusMessage('Could not find realm', 'error')
        else:
            self.config.removeRealm(realm)
            self.statusMessage('Removed realm')
        return self.request.RESPONSE.redirect('./@@publisher-config')


class TestRealm(PublisherConfigletView):

    def __call__(self, *args, **kwargs):
        id = self.request.get('id', '')
        realm = self.getRealmById(id)
        if not realm:
            self.statusMessage(_(u'error_realm_not_found',
                                 default=u'Could not find realm'), 'error')
        else:
            responseText = sendRequestToRealm({}, realm,
                                              'publisher.testConnection')
            if responseText=='ok':
                self.statusMessage(_(u'info_realm_connection_okay',
                                     default=u'Connection okay'))
            else:
                self.statusMessage(
                    _(u'error_realm_connection_failed',
                      default=u'Connection to realm failed: ${msg}',
                      mapping=dict(msg=responseText.decode('utf-8'))),
                    type='error')
        return self.request.RESPONSE.redirect('./@@publisher-config')
