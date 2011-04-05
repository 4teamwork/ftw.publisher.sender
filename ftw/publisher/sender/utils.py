from ftw.publisher.core import communication
from ftw.publisher.core.states import ConnectionLost
from ftw.publisher.sender.persistence import Realm
from httplib import BadStatusLine
import base64
import os.path
import sys
import traceback
import urllib
import urllib2


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
    data = {'jsondata' : json}
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
    @param data:            dictionary of parameters to send within the HTTP request
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
    credentials = ':'.join([realm.username.encode('hex'), realm.password.encode('hex')])
    credentials = str(base64.encodestring(credentials)).strip()
    headers = {
        'User-Agent'            : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
        'Content-Type'          : 'application/x-www-form-urlencoded',
        'Cookie'                : '__ac=' + credentials,
        }
    request = urllib2.Request(url, urllib.urlencode(data), headers)
    response = urllib2.urlopen(request)
    return response.read()
