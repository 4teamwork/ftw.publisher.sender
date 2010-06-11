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

from zope import schema
from zope.interface import Interface

class IRealmSchema(Interface):
    active = schema.Bool(
        title = u'Active',
        )
    url = schema.URI(
        title = u'URL to the Plone-Site',
        )
    username = schema.TextLine(
        title = u'Username',
        )
    password = schema.Password(
        title = u'Password',
        )

class IEditRealmSchema(IRealmSchema):

    id = schema.TextLine(
        title = u'id',
        )
    password = schema.Password(
        title = u'Password',
        required = False,
        )

