#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2015, 2016, 2017 Guenter Bartsch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Zamia-Prolog error classes
#

class PrologRuntimeError(Exception):
    def __init__(self, value, location=None):
        self.value = value
        self.location = location
    def __str__(self):
        if self.location:
            return str(self.location) + ':' + repr(self.value)
        return repr(self.value)
    def __unicode__(self):
        if self.location:
            return unicode(self.location) + u':' + self.value
        return self.value

# parser throws this at compile-time:
class PrologError(Exception):
    def __init__(self, value, location=None):
        self.value    = value
        self.location = location
    def __str__(self):
        if self.location:
            return str(self.location) + ':' + repr(self.value)
        return repr(self.value)
    def __unicode__(self):
        if self.location:
            return unicode(self.location) + u':' + self.value
        return self.value

