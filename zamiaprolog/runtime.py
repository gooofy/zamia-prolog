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
# Zamia-Prolog engine
#
# based on http://openbookproject.net/py4fun/prolog/prolog3.html by Chris Meyers
#

import os
import sys
import logging
import codecs
import re
import copy

from logic        import *
from builtins     import *
from errors       import *
from nltools.misc import limit_str

def prolog_unary_plus  (a) : return NumberLiteral(a)
def prolog_unary_minus (a) : return NumberLiteral(-a)

unary_operators = {'+': prolog_unary_plus, 
                   '-': prolog_unary_minus}

def prolog_binary_add (a,b) : return NumberLiteral(a + b)
def prolog_binary_sub (a,b) : return NumberLiteral(a - b)
def prolog_binary_mul (a,b) : return NumberLiteral(a * b)
def prolog_binary_div (a,b) : return NumberLiteral(a / b)
def prolog_binary_mod (a,b) : return NumberLiteral(a % b)

binary_operators = {'+'  : prolog_binary_add, 
                    '-'  : prolog_binary_sub, 
                    '*'  : prolog_binary_mul,
                    '/'  : prolog_binary_div,
                    'mod': prolog_binary_mod,
                    }

builtin_specials = set(['is', 'cut', 'fail', 'not', 'or', 'and'])

class PrologGoal:

    def __init__ (self, head, terms, parent=None, env={}, negate=False, inx=0, location=None) :

        assert type(terms) is list
        assert location

        self.head     = head
        self.terms    = terms
        self.parent   = parent
        self.env      = copy.deepcopy(env)
        self.negate   = negate
        self.inx      = inx
        self.location = location

    def __unicode__ (self):
        
        res = u'!goal ' if self.negate else u'goal '

        if self.head:
            res += unicode(self.head)
        else:
            res += u'TOP'
        res += ' '

        for i, t in enumerate(self.terms):
            if i == self.inx:
                 res += u"**"
            res += unicode(t) + u' '

        res += u'env=%s' % unicode(self.env)

        return res

    def __str__ (self) :
        return unicode(self).encode('utf8')

    def __repr__ (self):
        return 'PrologGoal(%s)' % str(self)

    def get_depth (self):
        if not self.parent:
            return 0
        return self.parent.get_depth() + 1

class PrologRuntime(object):

    def register_builtin (self, name, builtin):
        self.builtins[name] = builtin

    def register_builtin_function (self, name, fn):
        self.builtin_functions[name] = fn

    def set_trace(self, trace):
        self.trace = trace

    def __init__(self, db):
        self.db                = db
        self.builtins          = {}
        self.builtin_functions = {}
        self.trace             = False

        # arithmetic

        self.register_builtin('>',               builtin_larger)
        self.register_builtin('<',               builtin_smaller)
        self.register_builtin('=<',              builtin_smaller_or_equal)
        self.register_builtin('>=',              builtin_larger_or_equal)
        self.register_builtin('\\=',             builtin_non_equal)
        self.register_builtin('=',               builtin_equal)

        self.register_builtin('increment',       builtin_increment) # increment (?V, +I)
        self.register_builtin('decrement',       builtin_decrement) # decrement (?V, +D)

        # strings

        self.register_builtin('sub_string',      builtin_sub_string)
        self.register_builtin('atom_chars',      builtin_atom_chars)

        # time and date

        self.register_builtin('date_time_stamp', builtin_date_time_stamp)
        self.register_builtin('stamp_date_time', builtin_stamp_date_time)
        self.register_builtin('get_time',        builtin_get_time)

        # I/O

        self.register_builtin('write',           builtin_write)          # write (+Term)
        self.register_builtin('nl',              builtin_nl)

        # lists

        self.register_builtin('list_contains',   builtin_list_contains)
        self.register_builtin('list_nth',        builtin_list_nth)
        self.register_builtin('list_slice',      builtin_list_slice)     # list_slice (+Idx1, +Idx2, +List, -Slice) 
        self.register_builtin('list_append',     builtin_list_append)    # list_append (?List, +Element)
        self.register_builtin('list_str_join',   builtin_list_str_join)  # list_str_join (+Glue, +List, -Str)

        # dicts

        self.register_builtin('dict_put',        builtin_dict_put)       # dict_put (?Dict, +Key, +Value)
        self.register_builtin('dict_get',        builtin_dict_get)       # dict_get (+Dict, ?Key, -Value)

        # assert, rectract...

        self.register_builtin('assertz',         builtin_assertz)        # assertz (+P)
        self.register_builtin('gensym',          builtin_gensym)         # gensym (+Root, -Unique)


        #
        # builtin functions
        #

        self.register_builtin_function ('format_str', builtin_format_str)

        # lists

        self.register_builtin_function ('list_max',   builtin_list_max)
        self.register_builtin_function ('list_min',   builtin_list_min)
        self.register_builtin_function ('list_sum',   builtin_list_sum)
        self.register_builtin_function ('list_avg',   builtin_list_avg)
        self.register_builtin_function ('list_len',   builtin_list_len)

    def prolog_eval (self, term, env, location):      # eval all variables within a term to constants

        if isinstance(term, Predicate):

            # unary builtin ?

            if len(term.args) == 1:
                op = unary_operators.get(term.name)
                if op:

                    a = self.prolog_eval(term.args[0], env, location)

                    if not isinstance (a, NumberLiteral):
                        return None

                    return op(a.f)

            # binary builtin ?

            op = binary_operators.get(term.name)
            if op:
                if len(term.args) != 2:
                    return None

                a = self.prolog_eval(term.args[0], env, location)

                if not isinstance (a, NumberLiteral):
                    return None

                b = self.prolog_eval(term.args[1], env, location)

                if not isinstance (b, NumberLiteral):
                    return None

                return op(a.f, b.f)

            # engine-provided builtin function ?

            if term.name in self.builtin_functions:
                return self.builtin_functions[term.name](term, env, self, location)

        if isinstance (term, Literal):
            return term
        if isinstance (term, MacroCall):
            return term
        if isinstance (term, Variable):
            ans = env.get(term.name)
            if not ans:
                return None
            else: 
                return self.prolog_eval(ans, env, location)
        args = []
        for arg in term.args : 
            a = self.prolog_eval(arg, env, location)
            if not a: 
                return None
            args.append(a)
        return Predicate(term.name, args)

    # helper functions (used by builtin predicates)
    def prolog_get_int(self, term, env, location):

        t = self.prolog_eval (term, env, location)

        if not isinstance (t, NumberLiteral):
            raise PrologRuntimeError('Integer expected, %s found instead.' % term.__class__, location)
        return int(t.f)

    def prolog_get_float(self, term, env, location):

        t = self.prolog_eval (term, env, location)

        if not isinstance (t, NumberLiteral):
            raise PrologRuntimeError('Float expected, %s found instead.' % term.__class__, location)
        return t.f

    def prolog_get_string(self, term, env, location):

        t = self.prolog_eval (term, env, location)

        if not isinstance (t, StringLiteral):
            raise PrologRuntimeError('String expected, %s found instead.' % t.__class__, location)
        return t.s

    def prolog_get_literal(self, term, env, location):

        t = self.prolog_eval (term, env, location)

        if not isinstance (t, Literal):
            raise PrologRuntimeError('Literal expected, %s %s found instead.' % (t.__class__, t), location)
        return t.get_literal()

    def prolog_get_bool(self, term, env, location):

        t = self.prolog_eval (term, env, location)

        if not isinstance(t, Predicate):
            raise PrologRuntimeError('Boolean expected, %s found instead.' % term.__class__, location)
        return t.name == 'true'

    def prolog_get_list(self, term, env, location):

        t = self.prolog_eval (term, env, location)

        if not isinstance(t, ListLiteral):
            raise PrologRuntimeError('List expected, %s found instead.' % term.__class__, location)
        return t

    def prolog_get_dict(self, term, env, location):

        t = self.prolog_eval (term, env, location)

        if not isinstance(t, DictLiteral):
            raise PrologRuntimeError('Dict expected, %s found instead.' % term.__class__, location)
        return t

    def prolog_get_variable(self, term, env, location):

        if not isinstance(term, Variable):
            raise PrologRuntimeError('Variable expected, %s found instead.' % term.__class__, location)
        return term.name

    def prolog_get_constant(self, term, env, location):

        t = self.prolog_eval (term, env, location)

        if not isinstance(t, Predicate):
            raise PrologRuntimeError('Constant expected, %s found instead.' % term.__class__, location)
        if len(t.args) >0:
            raise PrologRuntimeError('Constant expected, %s found instead.' % unicode(t), location)
        return t.name

    def prolog_get_predicate(self, term, env, location):

        t = self.prolog_eval (term, env, location)

        if t:
            if not isinstance(t, Predicate):
                raise PrologRuntimeError(u'Predicate expected, %s (%s) found instead.' % (unicode(t), t.__class__), location)
            return t

        if not isinstance(term, Predicate):
            raise PrologRuntimeError(u'Predicate expected, %s (%s) found instead.' % (unicode(term), term.__class__), location)

        return term

    # A Goal is a rule in at a certain point in its computation. 
    # env contains definitions (so far), inx indexes the current term
    # being satisfied, parent is another Goal which spawned this one
    # and which we will unify back to when this Goal is complete.

    def _unify (self, src, srcEnv, dest, destEnv, location) :
        "update dest env from src. return true if unification succeeds"
        # logging.debug("Unify %s %s to %s %s" % (src, srcEnv, dest, destEnv))

        # FIXME: ?!? if src.pred == '_' or dest.pred == '_' : return sts(1,"Wildcard")

        if isinstance (src, Variable):
            srcVal = self.prolog_eval(src, srcEnv, location)
            if not srcVal: 
                return True 
            else: 
                return self._unify(srcVal, srcEnv, dest, destEnv, location)

        if isinstance (dest, Variable):
            destVal = self.prolog_eval(dest, destEnv, location)     # evaluate destination
            if destVal: 
                return self._unify(src, srcEnv, destVal, destEnv, location)
            else:
                destEnv[dest.name] = self.prolog_eval(src, srcEnv, location)
                return True                         # unifies. destination updated

        elif isinstance (src, Literal):
            srcVal  = self.prolog_eval(src, srcEnv, location)
            destVal = self.prolog_eval(dest, destEnv, location)
            return srcVal == destVal
            
        elif isinstance (dest, Literal):
            return False

        elif src.name != dest.name:
            return False
        elif len(src.args) != len(dest.args): 
            return False
        else:
            dde = copy.deepcopy(destEnv)
            for i in range(len(src.args)):
                if not self._unify(src.args[i], srcEnv, dest.args[i], dde, location):
                    return False

            # always unify implicit overlay variable:

            if ASSERT_OVERLAY_VAR_NAME in srcEnv:
                dde[ASSERT_OVERLAY_VAR_NAME] = srcEnv[ASSERT_OVERLAY_VAR_NAME]

            destEnv.update(dde)
            return True

    def _trace (self, label, goal):

        if not self.trace:
            return

        # logging.debug ('label: %s, goal: %s' % (label, unicode(goal)))

        depth = goal.get_depth()
        # ind = depth * '  ' + len(label) * ' '

        res = u'!' if goal.negate else u''

        if goal.head:
            res += limit_str(unicode(goal.head), 60)
        else:
            res += u'TOP'
        res += ' '

        for i, t in enumerate(goal.terms):
            if i == goal.inx:
                 res += u" -> " + limit_str(unicode(t), 60)

        res += ' [' + unicode(goal.location) + ']'

        # indent = depth*'  ' + len(label) * ' '
        indent = depth*'  '

        logging.info(u"%s %s: %s" % (indent, label, res))
     
        for k in sorted(goal.env):
            if k != ASSERT_OVERLAY_VAR_NAME:
                logging.info(u"%s   %s=%s" % (indent, k, limit_str(repr(goal.env[k]), 100)))

        if ASSERT_OVERLAY_VAR_NAME in goal.env:
            for k in sorted(goal.env[ASSERT_OVERLAY_VAR_NAME]):
                for clause in goal.env[ASSERT_OVERLAY_VAR_NAME][k]:
                    logging.info(u"%s   [O] %s" % (indent, limit_str(unicode(clause), 100)))


            
        # import pdb; pdb.set_trace()

        # res += u'env=%s' % unicode(self.env)
        
    def _trace_fn (self, label, env):

        if not self.trace:
            return

        indent = '              '

        logging.info(u"%s %s" % (indent, label))
     
        # import pdb; pdb.set_trace()

        for k in sorted(env):
            logging.info(u"%s   %s=%s" % (indent, k, limit_str(repr(env[k]), 80)))

    def _finish_goal (self, g, succeed, queue, solutions):

        while True:

            succ = not succeed if g.negate else succeed
            
            if succ:
                self._trace ('SUCCESS ', g)

                if g.parent == None :                   # Our original goal?
                    solutions.append(g.env)        # Record solution

                else: 
                    parent = copy.deepcopy(g.parent)    # Otherwise resume parent goal
                    self._unify (g.head, g.env,
                                 parent.terms[parent.inx], parent.env, g.location)
                    parent.inx = parent.inx+1           # advance to next goal in body
                    queue.insert(0, parent)             # let it wait its turn

                break

            else:
                self._trace ('FAIL ', g)

                if g.parent == None :                   # Our original goal?
                    break

                else: 
                    parent = copy.deepcopy(g.parent)    # Otherwise resume parent goal
                    self._unify (g.head, g.env,
                                 parent.terms[parent.inx], parent.env, g.location)
                    g       = parent
                    succeed = False

    def search (self, clause, env={}, err_on_missing=True):

        if clause.body is None:
            return [{}]

        if isinstance (clause.body, Predicate):
            if clause.body.name == 'and':
                terms = clause.body.args
            else:
                terms = [ clause.body ]
        else:
            raise PrologRuntimeError (u'search: expected predicate in body, got "%s" !' % unicode(clause))

        queue     = [ PrologGoal (clause.head, terms, env=env, location=clause.location) ]
        solutions = []

        while queue :
            g = queue.pop()                         # Next goal to consider

            self._trace ('CONSIDER', g)

            if g.inx >= len(g.terms) :              # Is this one finished?
                self._finish_goal (g, True, queue, solutions)
                continue

            # No. more to do with this goal.
            pred = g.terms[g.inx]                   # what we want to solve

            name = pred.name
                
            # FIXME: debug only
            # if name == 'ias':
            #     import pdb; pdb.set_trace()
            # import pdb; pdb.set_trace()

            if name in builtin_specials:
                if name == 'is' :

                    ques = self.prolog_eval(pred.args[0], g.env, g.location)
                    ans  = self.prolog_eval(pred.args[1], g.env, g.location)

                    if ques == None :
                        g.env[pred.args[0].name] = ans  # Set variable

                    elif ques != ans :                  # Mismatch, fail
                        self._finish_goal (g, False, queue, solutions)
                        continue                

                elif name == 'cut' : queue = [] # Zap the competition
                elif name == 'fail':            # Dont succeed
                    self._finish_goal (g, False, queue, solutions)
                    continue

                elif name == 'not':
                    # insert negated sub-guoal
                    queue.insert(0, PrologGoal(pred, pred.args, g, env=g.env, negate=True, location=g.location))
                    continue

                elif name == 'or':

                    # logging.debug ('   or clause detected.')

                    for subgoal in pred.args:
                        # logging.debug ('    subgoal: %s' % subgoal)
                        queue.insert(0, PrologGoal(pred, [subgoal], g, env=g.env, location=g.location))

                    continue

                elif name == 'and':
                    queue.insert(0, PrologGoal(pred, pred.args, g, env=g.env, location=g.location))
                    continue

                g.inx = g.inx + 1               # Succeed. resume self.
                queue.insert(0, g)
                continue

            # builtin predicate ?

            if pred.name in self.builtins:
                bindings = self.builtins[pred.name](g, self)
                if bindings:

                    self._trace ('SUCCESS FROM BUILTIN ', g)
    
                    g.inx = g.inx + 1
                    if type(bindings) is list:

                        for b in bindings:
                            new_env = copy.deepcopy(g.env)
                            new_env.update(b)
                            queue.insert(0, PrologGoal(g.head, g.terms, parent=g.parent, env=new_env, inx=g.inx, location=g.location))

                    else:
                        queue.insert (0, g)

                else:
                    self._finish_goal (g, False, queue, solutions)

                continue

            # Not special. look up in rule database

            clauses = self.db.lookup(pred.name, g.env.get(ASSERT_OVERLAY_VAR_NAME))

            if len(clauses) == 0: 
                if err_on_missing:
                    raise PrologRuntimeError ('Failed to find predicate "%s" !' % pred.name, g.location)
                else:
                    # simply fail
                    self._finish_goal (g, False, queue, solutions)
                    continue


            success = False

            for clause in clauses:

                if len(clause.head.args) != len(pred.args): 
                    continue

                # logging.debug('clause: %s' % clause)

                # queue up child subgoal

                if clause.body:
                    child = PrologGoal(clause.head, [clause.body], g, location=clause.location)
                else:
                    child = PrologGoal(clause.head, [], g, location=clause.location)

                ans = self._unify (pred, g.env, clause.head, child.env, g.location)
                if ans:                             # if unifies, queue it up
                    queue.insert(0, child)
                    success = True
                    # logging.debug ("Queue %s" % str(child))

            if not success:
                # make sure we explicitly fail for proper negation support
                self._finish_goal (g, False, queue, solutions)


        return solutions

    def search_predicate(self, name, args, env={}, location=None, err_on_missing=True):

        """ convenience function: build Clause/Predicate structure, translate python strings in args
            into Predicates/Variables by Prolog conventions (lowercase: predicate, uppercase: variable) """

        if not location:
            location = SourceLocation('<input>', 0, 0)

        mapped_args = []
        for arg in args:
            if not isinstance(arg, basestring):
                mapped_args.append(arg)
                continue
            if arg[0].isupper():
                mapped_args.append(Variable(arg))
            else:
                mapped_args.append(Predicate(arg))

        solutions = self.search(Clause(body=Predicate(name, mapped_args), location=location), env=env, err_on_missing=err_on_missing)

        return solutions

