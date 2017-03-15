#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2017 Guenter Bartsch, Heiko Schaefer
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

import unittest
import logging
import codecs

from nltools import misc
from zamiaprolog.logicdb import LogicDB
from zamiaprolog.parser  import PrologParser
from zamiaprolog.runtime import PrologRuntime
from zamiaprolog.logic   import NumberLiteral

UNITTEST_MODULE = 'unittests'

recorded_moves = []

def record_move(g, rt):

    global recorded_moves

    rt._trace ('CALLED BUILTIN record_move', g)

    pred = g.terms[g.inx]
    args = pred.args
    if len(args) != 2:
        raise PrologRuntimeError('record_move: 2 args expected.')

    arg_from  = rt.prolog_eval(args[0], g.env)
    arg_to    = rt.prolog_eval(args[1], g.env) 

    recorded_moves.append((arg_from, arg_to))
        
    return True

def multi_binder(g, rt):

    global recorded_moves

    rt._trace ('CALLED BUILTIN multi_binder', g)

    pred = g.terms[g.inx]
    args = pred.args
    if len(args) != 2:
        raise PrologRuntimeError('multi_binder: 2 args expected.')

    var_x  = rt.prolog_get_variable(args[0], g.env)
    var_y  = rt.prolog_get_variable(args[1], g.env) 

    res = []
    for x in range(2):

        lx = NumberLiteral(x)

        for y in range(2):
            ly = NumberLiteral(y)

            res.append({var_x: lx, var_y: ly})

    return res

class TestEmbeddings (unittest.TestCase):

    def setUp(self):

        config = misc.load_config('.airc')

        #
        # db, store
        #

        db_url = config.get('db', 'url')
        # db_url = 'sqlite:///tmp/foo.db'

        # setup compiler + environment

        self.db     = LogicDB(db_url, echo=False)
        self.parser = PrologParser()
        self.rt     = PrologRuntime(self.db)

        # self.rt.set_trace(True)

        self.db.clear_module(UNITTEST_MODULE)

    #@unittest.skip("temporarily disabled")
    def test_custom_builtins(self):

        global recorded_moves

        self.parser.compile_file('samples/hanoi2.pl', UNITTEST_MODULE, self.db)

        clause = self.parser.parse_line_clause_body('move(3,left,right,center)')
        logging.debug('clause: %s' % clause)

        # register our custom builtin
        recorded_moves = []
        self.rt.register_builtin('record_move', record_move)

        solutions = self.rt.search(clause)
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 1)

        self.assertEqual (len(recorded_moves), 7)

    #@unittest.skip("temporarily disabled")
    def test_custom_builtin_multiple_bindings(self):

        self.rt.register_builtin('multi_binder', multi_binder)

        clause = self.parser.parse_line_clause_body('multi_binder(X,Y)')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause)
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 4)

    def _custom_directive(self, module_name, clause, user_data):
        # logging.debug('custom_directive has been run')
        self.assertEqual (len(clause.head.args), 3)
        self.assertEqual (unicode(clause.head.args[0]), u'abc')
        self.assertEqual (clause.head.args[1].f, 42)
        self.assertEqual (clause.head.args[2].s, u'foo')

        self.directive_mark = True

    #@unittest.skip("temporarily disabled")
    def test_custom_directives(self):

        self.parser.register_directive('custom_directive', self._custom_directive, None)
        self.directive_mark = False

        # self.parser.compile_file('samples/dir.pl', UNITTEST_MODULE, self.db)
        clauses = self.parser.parse_line_clauses('custom_directive(abc, 42, \'foo\').')

        self.assertEqual (self.directive_mark, True)


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    # logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    unittest.main()

