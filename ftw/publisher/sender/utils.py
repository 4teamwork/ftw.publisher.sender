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

# global imports
import os.path
import urllib
import urllib2
import base64

# publisher imports
from ftw.publisher.sender.persistence import Realm
from ftw.publisher.core import communication


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
    html = sendRequestToRealm(data, realm, serverAction)
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


def aggressive_decode(value, encoding='utf-8'):
    if isinstance(value, unicode):
        return value
    other_encodings = filter(lambda e:e is not encoding, [
            'utf8',
            'iso-8859-1',
            'latin1',
            ])
    encodings = [encoding] + other_encodings
    if not isinstance(value, str):
        value = str(value)
    for enc in encodings:
        try:
            return value.decode(enc)
        except UnicodeDecodeError:
            pass
    raise


def recursive_aggressive_decode(value):
    # str types
    if isinstance(value, str) or isinstance(value, unicode):
        return aggressive_decode(value)

    # lists tuples sets
    if type(value) in (list, tuple, set):
        nval = []
        for sval in value:
            nval.append(recursive_aggressive_decode(sval))
        if isinstance(value, tuple):
            return tuple(nval)
        elif isinstance(value, set):
            return set(nval)
        return nval

    # dicts
    if isinstance(value, dict):
        nval = {}
        for key, sval in value.items():
            key = recursive_aggressive_decode(key)
            sval = recursive_aggressive_decode(sval)
            nval[key] = sval
        return nval

    # others
    return value
