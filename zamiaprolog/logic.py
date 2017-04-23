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
import json

class JSONLogic:

    """ just a base class that indicates to_dict() and __init__(json_dict) are supported
        for JSON (de)-serialization """

    def to_dict(self):
        raise Exception ("to_dict is not implemented, but should be!")

class SourceLocation(JSONLogic):

    def __init__ (self, fn=None, line=None, col=None, json_dict=None):
        if json_dict:
            self.fn   = json_dict['fn']
            self.line = json_dict['line']
            self.col  = json_dict['col']
        else:
            self.fn   = fn
            self.line = line
            self.col  = col

    def __str__(self):
        return '%s: line=%d, col=%d' % (self.fn, self.line, self.col)

    def __unicode__(self):
        return u'%s: line=%d, col=%d' % (self.fn, self.line, self.col)

    def __repr__(self):
        return 'SourceLocation(fn=%s, line=%d, col=%d)' % (self.fn, self.line, self.col)

    def to_dict(self):
        return {'pt': 'SourceLocation', 'fn': self.fn, 'line': self.line, 'col': self.col}

class Literal(JSONLogic):

    def __unicode__(self):
        return "<LITERAL>"

    def __str__ (self):
        return "<LITERAL>"

class StringLiteral(Literal):

    def __init__(self, s=None, json_dict=None):
        if json_dict:
            self.s = json_dict['s']
        else:
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
        return not isinstance(b, StringLiteral) or self.s != b.s

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

    def to_dict(self):
        return {'pt': 'StringLiteral', 's': self.s}

class NumberLiteral(Literal):

    def __init__(self, f=None, json_dict=None):
        if json_dict:
            self.f = json_dict['f']
        else:
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
        return not isinstance(b, NumberLiteral) or self.f != b.f

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

    def to_dict(self):
        return {'pt': 'NumberLiteral', 'f': self.f}

class ListLiteral(Literal):

    def __init__(self, l=None, json_dict=None):
        if json_dict:
            self.l = json_dict['l']
        else:
            self.l = l

    def __unicode__(self):
        return repr(self.l)

    def __eq__(self, other):

        if not isinstance(other, ListLiteral):
            return False

        return other.l == self.l

    def __ne__(self, other):

        if not isinstance(other, ListLiteral):
            return True

        return other.l != self.l

    def get_literal(self):
        return self.l

    def __unicode__(self):
        return unicode(self.l)

    def __str__(self):
        return str(self.l)

    def __repr__(self):
        return repr(self.l)

    def to_dict(self):
        return {'pt': 'ListLiteral', 'l': self.l}

class Variable(JSONLogic):

    def __init__(self, name=None, json_dict=None):
        if json_dict:
            self.name = json_dict['name']
        else:
            self.name = name
  
    def __str__(self):
        return self.name.encode('utf8')

    def __unicode__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, Variable) and other.name == self.name

    def __hash__(self):
        return hash(self.name)

    def to_dict(self):
        return {'pt': 'Variable', 'name': self.name}

class Predicate(JSONLogic):

    def __init__(self, name=None, args=None, json_dict=None):

        if json_dict:
            self.name  = json_dict['name']
            self.args  = json_dict['args']

        else:
            self.name  = name
            self.args  = args if args else []
  
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

    def to_dict(self):
        return {'pt'  : 'Predicate', 
                'name': self.name, 
                'args': map(lambda a: a.to_dict(), self.args)
               }

class Clause(JSONLogic):

    def __init__(self, head=None, body=None, location=None, json_dict=None):
        if json_dict:
            self.head     = json_dict['head'] 
            b = json_dict['body']
            self.body     = None if b =='None' else b
            l = json_dict['location']
            self.location = None if l == 'None' else l
        else:
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

    def to_dict(self):
        return {'pt'      : 'Clause', 
                'head'    : self.head.to_dict(),
                'body'    : self.body.to_dict() if self.body else 'None',
                'location': self.location.to_dict(),
               }

class MacroCall:

    def __init__(self, name, pred):
        self.name = name
        self.pred = pred

    def __str__(self):
        return unicode(self).encode('utf8')

    def __unicode__(self):
        return u'@' + unicode(self.name) + u':' + unicode(self.pred)

    def __repr__(self):
        return 'MacroCall(%s, %s)' % (self.name, self.pred)

#
# JSON interface
#

class PrologJSONEncoder(json.JSONEncoder):

    def default(self, o):
        
        if isinstance (o, JSONLogic):
            return o.to_dict()

        return json.JSONEncoder.default(self, o)

_prolog_json_encoder = PrologJSONEncoder()

def prolog_to_json(pl):
    return _prolog_json_encoder.encode(pl)

def _prolog_from_json(o):

    # import pdb; pdb.set_trace()

    if o == 'None':
        return None

    if o['pt'] == 'Clause':
        return Clause(json_dict=o)
    if o['pt'] == 'Predicate':
        return Predicate(json_dict=o)
    if o['pt'] == 'StringLiteral':
        return StringLiteral (json_dict=o)
    if o['pt'] == 'NumberLiteral':
        return NumberLiteral (json_dict=o)
    if o['pt'] == 'ListLiteral':
        return ListLiteral (json_dict=o)
    if o['pt'] == 'Variable':
        return Variable (json_dict=o)
    if o['pt'] == 'SourceLocation':
        return SourceLocation (json_dict=o)

    raise PrologRuntimeError('cannot convert from json: %s .' % repr(o))

def json_to_prolog(jstr):
    return json.JSONDecoder(object_hook = _prolog_from_json).decode(jstr)

