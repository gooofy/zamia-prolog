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
from zamiaprolog.logic   import *
from zamiaprolog.errors  import PrologError, PrologRuntimeError

UNITTEST_MODULE = 'unittests'

class TestZamiaProlog (unittest.TestCase):

    def setUp(self):

        config = misc.load_config('.airc')

        #
        # db, store
        #

        db_url = config.get('db', 'url')
        # db_url = 'sqlite:///tmp/foo.db'

        # setup compiler + environment

        self.db     = LogicDB(db_url)
        self.parser = PrologParser()
        self.rt     = PrologRuntime(self.db)

        self.db.clear_module(UNITTEST_MODULE)

    # @unittest.skip("temporarily disabled")
    def test_parser(self):

        error_catched = False

        try:

            clause = self.parser.parse_line_clause_body('say_eoa(en, "Kids are the best')
            logging.debug('clause: %s' % clause)
        except PrologError as e:
            error_catched = True

        self.assertEqual(error_catched, True)

    # @unittest.skip("temporarily disabled")
    def test_parse_line_clauses(self):

        line = 'time_span(TE) :- date_time_stamp(+(D, 1.0)).'

        tree = self.parser.parse_line_clauses(line)
        logging.debug (unicode(tree[0].body))
        self.assertEqual (tree[0].body.name, 'date_time_stamp')
        self.assertEqual (tree[0].head.name, 'time_span')

        line = 'time_span(tomorrow, TS, TE) :- context(currentTime, T), stamp_date_time(T, date(Y, M, D, H, Mn, S, "local")), date_time_stamp(date(Y, M, +(D, 1.0), 0.0, 0.0, 0.0, "local"), TS), date_time_stamp(date(Y, M, +(D, 1.0), 23.0, 59.0, 59.0, "local"), TE).'

        tree = self.parser.parse_line_clauses(line)
        logging.debug (unicode(tree[0].body))
        self.assertEqual (tree[0].head.name, 'time_span')
        self.assertEqual (tree[0].body.name, 'and')
        self.assertEqual (len(tree[0].body.args), 4)

    # @unittest.skip("temporarily disabled")
    def test_kb1(self):

        self.assertEqual (len(self.db.lookup('party')), 0)

        self.parser.compile_file('samples/kb1.pl', UNITTEST_MODULE, self.db)

        self.assertEqual (len(self.db.lookup('party')), 1)

        clause = self.parser.parse_line_clause_body('woman(X)')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause)
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 3)

        clause = self.parser.parse_line_clause_body('party')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause)
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 1)

        clause = self.parser.parse_line_clause_body('woman(fred)')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause)
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 0)

    # @unittest.skip("temporarily disabled")
    def test_parse_to_string(self):

        line = u'time_span(c, X, Y) :- p1(c), p2(X, Y); p3(c); p4.'

        tree = self.parser.parse_line_clauses(line)
        logging.debug (unicode(tree[0].body))
        self.assertEqual (unicode(tree[0]), line)


    # @unittest.skip("temporarily disabled")
    def test_or(self):

        self.parser.compile_file('samples/or_test.pl', UNITTEST_MODULE, self.db)

        # self.rt.set_trace(True)

        solutions = self.rt.search_predicate('woman', ['X'])
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 3)

        solutions = self.rt.search_predicate('human', ['X'])
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 8)

    def test_or_toplevel(self):

        self.parser.compile_file('samples/or_test.pl', UNITTEST_MODULE, self.db)

        self.rt.set_trace(True)

        clause = self.parser.parse_line_clause_body(u'woman(mary); woman(jody)')
        logging.debug(u'clause: %s' % clause)
        solutions = self.rt.search(clause)
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 1)


    def test_var_access(self):

        # set var X from python:

        clause = self.parser.parse_line_clause_body('Y is X*X')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause, {'X': NumberLiteral(3)})
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 1)

        # access prolog result Y from python:

        self.assertEqual (solutions[0]['Y'].f, 9)

    def test_list_equality(self):

        clause = self.parser.parse_line_clause_body('[] is []')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause, {})
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 1)

        clause = self.parser.parse_line_clause_body('[1] is []')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause, {})
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 0)

        clause = self.parser.parse_line_clause_body('909442800.0 is []')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause, {})
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 0)

        clause = self.parser.parse_line_clause_body('[1,2,3] = [1,2,3]')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause, {})
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 1)

        clause = self.parser.parse_line_clause_body('[1,2,3] \\= [1,2,3,4,5]')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause, {})
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 1)

    def test_is(self):

        clause = self.parser.parse_line_clause_body('GENDER is "blubber", GENDER is wde:Male')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause, {})
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 0)

    def test_clauses_location(self):

        # this will trigger a runtime error since Y is not bound, 
        # but format_str requires a bound value
        clause = self.parser.parse_line_clause_body('X is format_str("%s", Y)')
        logging.debug('clause: %s' % clause)
        try:
            solutions = self.rt.search(clause, {})
            self.fail("we should have seen a runtime error here")
        except PrologRuntimeError as e:
            self.assertEqual (e.location.line, 1)
            self.assertEqual (e.location.col, 26)

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    unittest.main()

