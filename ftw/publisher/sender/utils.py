from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from Products.statusmessages.interfaces import IStatusMessage
from ftw.publisher.core import communication
from ftw.publisher.core.states import ConnectionLost
from ftw.publisher.sender.persistence import Realm
from httplib import BadStatusLine
import base64
import os.path
import sys
import traceback
import transaction
import urllib
import urllib2


def _get_savepoint_ids():
    """Returns a list of ids of all currently active savepoints.
    """
    trans = transaction.get()
    if not trans._savepoint2index:
        return None
    else:
        return map(id, trans._savepoint2index)


def add_transaction_aware_status_message(request, *args, **kwargs):
    savepoint_ids = _get_savepoint_ids()

    def _add_status_message_hook(success, request, *args, **kwargs):
        if not success:
            return

        if savepoint_ids != _get_savepoint_ids():
            # There were rollbacked savepoints.
            # We assume that this was the integrity check which was rolled
            # back so we do not set the status message.
            # Since the integrity check works by deleting items and rolling
            # back the savepoint and status messages are not transaction
            # save we need to cancel adding the status message here.
            return

        IStatusMessage(request).addStatusMessage(*args, **kwargs)

    transaction.get().addAfterCommitHook(
        _add_status_message_hook, args=[request] + list(args), kws=kwargs)


def sendJsonToRealm(json, realm, serverAction):
    """
    Sends the json data to a realm with the given serverAction and
    parses the response.
    @param json:            JSON data
    @type json:             string
    @param realm:           Realm object of the target instance
    @type realm:            Realm
    @param serverAction:    Name of the BrowserView on the target instance
    @type serverAction:     string
    @return:                A CommunicationState
    @rtype:                 CommunicationState
    """
    if not isinstance(realm, Realm):
        TypeError('Excpected Realm instance')
    data = {'jsondata': json}
    try:
        html = sendRequestToRealm(data, realm, serverAction)
    except BadStatusLine:
        exc = ''.join(traceback.format_exception(*sys.exc_info()))
        return ConnectionLost(exc)
    return communication.parseResponse(html)


def sendRequestToRealm(data, realm, serverAction):
    """
    Makes a HTTP-Request to a realm and sends the given data on
    the provided serverAction
    @param data:            dictionary of parameters to send within the
                            HTTP request
    @type data:             dict
    @param realm:           Realm object of the target instance
    @type realm:            Realm
    @param serverAction:    Name of the BrowserView on the target instance
    @type serverAction:     string
    @return:                Response Text
    @rtype:                 string
    """
    if not isinstance(realm, Realm):
        TypeError('Excpected Realm instance')
    url = os.path.join(realm.url, serverAction)
    credentials = ':'.join([realm.username.encode('hex'),
                            realm.password.encode('hex')])
    credentials = str(base64.b64encode(credentials)).strip()
    headers = {
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': '__ac=' + credentials,
        }
    request = urllib2.Request(url, urllib.urlencode(data), headers)
    response = urllib2.urlopen(request)
    return response.read()


def is_temporary(obj, checkId=True):
    """Checks, whether an object is a temporary object (means it's in the
    `portal_factory`) or has no acquisition chain set up.
    Source: http://svn.plone.org/svn/collective/collective.indexing/trunk/collective/indexing/subscribers.py
    """
    parent = aq_parent(aq_inner(obj))
    if parent is None:
        return True
    if checkId and getattr(obj, 'getId', None):
        if getattr(aq_base(parent), obj.getId(), None) is None:
            return True
    isTemporary = getattr(obj, 'isTemporary', None)
    if isTemporary is not None:
        try:
            if obj.isTemporary():
                return True
        except TypeError:
            return True # `isTemporary` on the `FactoryTool` expects 2 args
    return False
