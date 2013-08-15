from Products.statusmessages.interfaces import IStatusMessage
from ftw.publisher.sender.workflows.interfaces import IConstraintDefinition
from ftw.publisher.sender.workflows.interfaces import IPublisherContextState
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.i18n import translate
from zope.interface import Interface
from zope.interface import implements


def message(msg):
    def _decorator(func):
        func._publisher_message = msg
        return func
    return _decorator


def error_on(*actions):
    def _decorator(func):
        func._publisher_error_on = actions
        return func
    return _decorator


def warning_on(*actions):
    def _decorator(func):
        func._publisher_warning_on = actions
        return func
    return _decorator


class ConstraintDefinition(object):
    implements(IConstraintDefinition)
    adapts(Interface, Interface)

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self._state = None

    def state(self):
        if self._state is None:
            self._state = getMultiAdapter(
                (self.context, self.request),
                IPublisherContextState)
        return self._state

    def is_action_allowed(self, action, silent=False):
        result = self.check_action(action)

        if not silent:
            msg = IStatusMessage(self.request)

            for error in result['errors']:
                msg.addStatusMessage(error, type='error')

            for warning in result['warnings']:
                msg.addStatusMessage(warning, type='warning')

        return len(result['errors']) == 0

    def check_action(self, action):
        result = {'errors': [],
                  'warnings': []}

        for item in self._get_checks_for(action):
            check_result = item['method']()
            if check_result is True:
                continue

            elif check_result is False:
                message = translate(item['message'], context=self.request)
                result[item['type']].append(message)

            else:
                for obj in check_result:
                    html = '<a href="%s">%s</a>' % (obj.absolute_url(),
                                                    obj.Title())

                    msg = item['message']
                    message = translate(
                        msg.decode('utf-8'),
                        default=msg.default,
                        domain=msg.domain,
                        mapping={'item': html.decode('utf-8')},
                        context=self.request)
                    result[item['type']].append(message)

        return result

    def _get_checks_for(self, action):
        for check in self._get_checks():
            item = {'message': check['message'],
                    'method': check['method']}

            if action in check['error_actions']:
                item['type'] = 'errors'
                yield item

            elif action in check['warning_actions']:
                item['type'] = 'warnings'
                yield item

    def _get_checks(self):
        for name in sorted(dir(self)):
            value = getattr(self, name, None)
            err = getattr(value, '_publisher_error_on', [])
            warn = getattr(value, '_publisher_warning_on', [])

            if not err and not warn:
                continue

            message = getattr(value, '_publisher_message', None)
            assert message, 'No message defined for check %s' % name

            yield {'error_actions': err,
                   'warning_actions': warn,
                   'message': message,
                   'method': value}
