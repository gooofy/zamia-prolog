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

from six                import python_2_unicode_compatible, text_type, string_types

from zamiaprolog.errors import PrologError

class JSONLogic:

    """ just a base class that indicates to_dict() and __init__(json_dict) are supported
        for JSON (de)-serialization """

    def to_dict(self):
        raise PrologError ("to_dict is not implemented, but should be!")

@python_2_unicode_compatible
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
        return u'%s: line=%s, col=%s' % (self.fn, text_type(self.line), text_type(self.col))

    def __repr__(self):
        return 'SourceLocation(fn=%s, line=%d, col=%d)' % (self.fn, self.line, self.col)

    def to_dict(self):
        return {'pt': 'SourceLocation', 'fn': self.fn, 'line': self.line, 'col': self.col}

@python_2_unicode_compatible
class Literal(JSONLogic):

    def __str__(self):
        return u"<LITERAL>"

@python_2_unicode_compatible
class StringLiteral(Literal):

    def __init__(self, s=None, json_dict=None):
        if json_dict:
            self.s = json_dict['s']
        else:
            self.s = s

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

    def __str__(self):
        return u'"' + text_type(self.s.replace('"', '\\"')) + u'"'

    def __repr__(self):
        return u'StringLiteral(' + repr(self.s) + ')'

    def to_dict(self):
        return {'pt': 'StringLiteral', 's': self.s}

    def __hash__(self):
        return hash(self.s)

@python_2_unicode_compatible
class NumberLiteral(Literal):

    def __init__(self, f=None, json_dict=None):
        if json_dict:
            self.f = json_dict['f']
        else:
            self.f = f

    def __str__(self):
        return text_type(self.f)

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

    def __hash__(self):
        return hash(self.f)

@python_2_unicode_compatible
class ListLiteral(Literal):

    def __init__(self, l=None, json_dict=None):
        if json_dict:
            self.l = json_dict['l']
        else:
            self.l = l

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

    def __str__(self):
        return u'[' + u','.join(map(lambda e: text_type(e), self.l)) + u']'

    def __repr__(self):
        return repr(self.l)

    def to_dict(self):
        return {'pt': 'ListLiteral', 'l': self.l}

@python_2_unicode_compatible
class DictLiteral(Literal):

    def __init__(self, d=None, json_dict=None):
        if json_dict:
            self.d = json_dict['d']
        else:
            self.d = d

    def __eq__(self, other):

        if not isinstance(other, DictLiteral):
            return False

        return other.d == self.d

    def __ne__(self, other):

        if not isinstance(other, DictLiteral):
            return True

        return other.d != self.d

    def get_literal(self):
        return self.d

    def __str__(self):
        return text_type(self.d)

    def __repr__(self):
        return repr(self.d)

    def to_dict(self):
        return {'pt': 'DictLiteral', 'd': self.d}

@python_2_unicode_compatible
class SetLiteral(Literal):

    def __init__(self, s=None, json_dict=None):
        if json_dict:
            self.s = json_dict['s']
        else:
            self.s = s

    def __eq__(self, other):

        if not isinstance(other, SetLiteral):
            return False

        return other.s == self.s

    def __ne__(self, other):

        if not isinstance(other, SetLiteral):
            return True

        return other.s != self.s

    def get_literal(self):
        return self.s

    def __str__(self):
        return text_type(self.s)

    def __repr__(self):
        return repr(self.s)

    def to_dict(self):
        return {'pt': 'SetLiteral', 's': self.s}

@python_2_unicode_compatible
class Variable(JSONLogic):

    def __init__(self, name=None, json_dict=None):
        if json_dict:
            self.name = json_dict['name']
        else:
            self.name = name
  
    def __repr__(self):
        return u'Variable(' + self.__unicode__() + u')'

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, Variable) and other.name == self.name

    def __hash__(self):
        return hash(self.name)

    def to_dict(self):
        return {'pt': 'Variable', 'name': self.name}

@python_2_unicode_compatible
class Predicate(JSONLogic):

    def __init__(self, name=None, args=None, json_dict=None):

        if json_dict:
            self.name  = json_dict['name']
            self.args  = json_dict['args']

        else:
            self.name  = name
            self.args  = args if args else []

    def __str__(self):
        if not self.args:
            return self.name

        # if self.name == 'and':
        #     return u', '.join(map(unicode, self.args))
        # if self.name == 'or':
        #     return u'; '.join(map(unicode, self.args))
        # elif self.name == 'and':
        #     return u', '.join(map(unicode, self.args))

        return u'%s(%s)' % (self.name, u', '.join(map(text_type, self.args)))
        #return '(' + self.name + ' ' + ' '.join( [str(arg) for arg in self.args]) + ')'

    def __repr__(self):
        return u'Predicate(' + text_type(self) + ')'

    def __eq__(self, other):
        return isinstance(other, Predicate) \
               and self.name == other.name  \
               and self.args == other.args

    def __ne__(self, other):
        if not isinstance(other, Predicate):
            return True
        if self.name != other.name:
            return True
        if self.args != other.args:
            return True
        return False

    def to_dict(self):
        return {'pt'  : 'Predicate', 
                'name': self.name, 
                'args': list(map(lambda a: a.to_dict(), self.args))
               }

    def __hash__(self):
        # FIXME hash args?
        return hash(self.name + u'/' + text_type(len(self.args)))

# helper function

def build_predicate(name, args):
    mapped_args = []
    for arg in args:
        if not isinstance(arg, string_types):
            if isinstance (arg, int):
                mapped_args.append(NumberLiteral(arg))
            elif isinstance (arg, float):
                mapped_args.append(NumberLiteral(arg))
            else:
                mapped_args.append(arg)
            continue
        if arg[0].isupper() or arg[0].startswith('_'):
            mapped_args.append(Variable(arg))
        else:
            mapped_args.append(Predicate(arg))
    return Predicate (name, mapped_args)

@python_2_unicode_compatible
class Clause(JSONLogic):

    def __init__(self, head=None, body=None, location=None, json_dict=None):
        if json_dict:
            self.head     = json_dict['head'] 
            self.body     = json_dict['body']
            self.location = json_dict['location']
        else:
            self.head     = head
            self.body     = body
            self.location = location

    def __str__(self):
        if self.body:
            return u'%s :- %s.' % (text_type(self.head), text_type(self.body))
        return text_type(self.head) + '.'

    def __repr__(self):
        return u'Clause(' + text_type(self) + u')'

    def __eq__(self, other):
        return (isinstance(other, Clause)
                and self.head == other.head
                and list(self.body) == list(other.body))

    def to_dict(self):
        return {'pt'      : 'Clause', 
                'head'    : self.head.to_dict(),
                'body'    : self.body.to_dict() if self.body else None,
                'location': self.location.to_dict(),
               }

@python_2_unicode_compatible
class MacroCall(JSONLogic):

    def __init__(self, name=None, pred=None, location=None, json_dict=None):
        if json_dict:
            self.name     = json_dict['name'] 
            self.pred     = json_dict['pred']
            self.location = json_dict['location']
        else:
            self.name     = name
            self.pred     = pred
            self.location = location

    def __str__(self):
        return u'@' + text_type(self.name) + u':' + text_type(self.pred)

    def __repr__(self):
        return 'MacroCall(%s, %s)' % (self.name, self.pred)

    def to_dict(self):
        return {'pt'      : 'MacroCall', 
                'name'    : self.name,
                'pred'    : self.pred,
                'location': self.location.to_dict(),
               }
#
# JSON interface
#

class PrologJSONEncoder(json.JSONEncoder):

    def default(self, o):
        
        if isinstance (o, JSONLogic):
            return o.to_dict()

        try:
            return json.JSONEncoder.default(self, o)
        except TypeError:
            import pdb; pdb.set_trace()


_prolog_json_encoder = PrologJSONEncoder()

def prolog_to_json(pl):
    return _prolog_json_encoder.encode(pl)

def _prolog_from_json(o):

    if o == None:
        return None

    if not 'pt' in o:
        # import pdb; pdb.set_trace()
        # raise PrologError('cannot convert from json: %s [pt missing] .' % repr(o))
        return o

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
    if o['pt'] == 'DictLiteral':
        return DictLiteral (json_dict=o)
    if o['pt'] == 'SetLiteral':
        return SetLiteral (json_dict=o)
    if o['pt'] == 'Variable':
        return Variable (json_dict=o)
    if o['pt'] == 'SourceLocation':
        return SourceLocation (json_dict=o)
    if o['pt'] == 'MacroCall':
        return MacroCall (json_dict=o)

    raise PrologError('cannot convert from json: %s .' % repr(o))

def json_to_prolog(jstr):
    return json.JSONDecoder(object_hook = _prolog_from_json).decode(jstr)

