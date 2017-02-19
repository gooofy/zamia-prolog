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
# classes that represent prolog clauses
#

import logging
import datetime
from dateutil.tz import tzlocal

class SourceLocation:

    def __init__ (self, fn, line, col):
        self.fn   = fn
        self.line = line
        self.col  = col

    def __str__(self):
        return '%s: line=%d, col=%d' % (self.fn, self.line, self.col)

    def __unicode__(self):
        return u'%s: line=%d, col=%d' % (self.fn, self.line, self.col)

    def __repr__(self):
        return 'SourceLocation(fn=%s, line=%d, col=%d)' % (self.fn, self.line, self.col)

class Literal:

    def __unicode__(self):
        return "<LITERAL>"

    def __str__ (self):
        return "<LITERAL>"

class StringLiteral(Literal):

    def __init__(self, s):
        self.s = s

    def __unicode__(self):
        return '"' + self.s + '"'

    def __eq__(self, b):
        return isinstance(b, StringLiteral) and self.s == b.s

    def __lt__(self, b):
        assert isinstance(b, StringLiteral)
        return self.s < b.s

    def __le__(self, b):
        assert isinstance(b, StringLiteral)
        return self.s <= b.s

    def __ne__(self, b):
        return isinstance(b, StringLiteral) and self.s != b.s

    def __ge__(self, b):
        assert isinstance(b, StringLiteral)
        return self.s >= b.s

    def __gt__(self, b):
        assert isinstance(b, StringLiteral)
        return self.s > b.s

    def get_literal(self):
        return self.s

    def __unicode__(self):
        return u'"' + unicode(self.s.replace('"', '\\"')) + u'"'

    def __str__(self):
        return '"' + str(self.s.replace('"', '\\"')) + '"'

    def __repr__(self):
        return u'StringLiteral(' + repr(self.s) + ')'

class NumberLiteral(Literal):

    def __init__(self, f):
        self.f = f

    def __unicode__(self):
        return unicode(self.f)

    def __str__(self):
        return str(self.f)

    def __repr__(self):
        return repr(self.f)

    def __eq__(self, b):
        return isinstance(b, NumberLiteral) and self.f == b.f

    def __lt__(self, b):
        assert isinstance(b, NumberLiteral)
        return self.f < b.f

    def __le__(self, b):
        assert isinstance(b, NumberLiteral)
        return self.f <= b.f

    def __ne__(self, b):
        return isinstance(b, NumberLiteral) and self.f != b.f

    def __ge__(self, b):
        assert isinstance(b, NumberLiteral)
        return self.f >= b.f

    def __gt__(self, b):
        assert isinstance(b, NumberLiteral)
        return self.f > b.f

    def __add__(self, b):
        assert isinstance(b, NumberLiteral) 
        return NumberLiteral(b.f + self.f)

    def __div__(self, b):
        assert isinstance(b, NumberLiteral) 
        return NumberLiteral(self.f / b.f)

    def get_literal(self):
        return self.f

class ListLiteral(Literal):

    def __init__(self, l):
        self.l = l

    def __unicode__(self):
        return repr(self.l)

    def __eq__(self, other):
        return isinstance(other, ListLiteral) and other.l == self.l

    def get_literal(self):
        return self.l

    def __unicode__(self):
        return unicode(self.l)

    def __str__(self):
        return str(self.l)

    def __repr__(self):
        return repr(self.l)

class Variable(object):

    counter = 0 
    @staticmethod
    def get_unused_var():
        v = Var('_var%d' % Var.counter)
        Var.counter += 1
        return v

    def __init__(self, name, row = False):
        self.name = name
        self.row  = row
  
    def __unicode__(self):
        return '@' + self.name if self.row else self.name

    def __eq__(self, other):
        return isinstance(other, Variable) and other.name == self.name

    def __hash__(self):
        return hash(self.name)

class Predicate:

    def __init__(self, name, args=None, uri = None):
        self.name  = name
        self.args  = args if args else []
        self.uri   = uri 
  
    def __str__(self):
        return unicode(self).encode('utf8')
    
    def __unicode__(self):
        if not self.args:
            return self.name

        if self.name == 'or':
            return u'; '.join(map(unicode, self.args))
        elif self.name == 'and':
            return u', '.join(map(unicode, self.args))

        return u'%s(%s)' % (self.name, u', '.join(map(unicode, self.args)))
        #return '(' + self.name + ' ' + ' '.join( [str(arg) for arg in self.args]) + ')'

    def __repr__(self):
        return u'Predicate(' + self.__unicode__() + ')'

    def __eq__(self, other):
        return (isinstance(other, Predicate)
                and self.name == other.name
                and list(self.args) == list(other.args))

class Clause:

    def __init__(self, head, body=None, location=None):
        self.head     = head
        self.body     = body
        self.location = location

    def __str__(self):
        if self.body:
            return u'%s :- %s.' % (str(self.head), str(self.body))
        return str(self.head) + '.'

    def __unicode__(self):
        if self.body:
            return u'%s :- %s.' % (unicode(self.head), unicode(self.body))
        return unicode(self.head) + '.'

    def __repr__(self):
        return u'Clause(' + unicode(self) + u')'

    def __eq__(self, other):
        return (isinstance(other, Clause)
                and self.head == other.head
                and list(self.body) == list(other.body))


class MacroCall:

    def __init__(self, name, pred):
        self.name = name
        self.pred = pred

    def __str__(self):
        return str(self.name) + '@' + str(self.pred)

    def __unicode__(self):
        return unicode(self.name) + u'@' + unicode(self.pred)

    def __repr__(self):
        return 'MacroCall(%s, %s)' % (self.name, self.pred)

