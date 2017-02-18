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
from halprolog.logicdb import LogicDB
from halprolog.parser  import PrologParser
from halprolog.runtime import PrologRuntime
from halprolog.logic   import *

class TestHALProlog (unittest.TestCase):

    def setUp(self):

        config = misc.load_config('.nlprc')

        #
        # db, store
        #

        db_url = config.get('db', 'url')
        # db_url = 'sqlite:///tmp/foo.db'

        # setup compiler + environment

        self.db     = LogicDB(db_url)
        self.parser = PrologParser()
        self.rt     = PrologRuntime(self.db)

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

        self.db.clear_module('unittests')

        self.assertEqual (len(self.db.lookup('party')), 0)

        self.parser.compile_file('samples/kb1.pl', 'unittests', self.db)

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

        self.db.clear_module('unittests')

        self.parser.compile_file('samples/or_test.pl', 'unittests', self.db)

        # self.rt.set_trace(True)

        clause = self.parser.parse_line_clause_body('woman(X)')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause)
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 3)

        clause = self.parser.parse_line_clause_body('human(X)')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause)
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 8)

    def test_var_access(self):

        # set var X from python:

        clause = self.parser.parse_line_clause_body('Y is X*X')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause, {'X': NumberLiteral(3)})
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 1)

        # access prolog result Y from python:

        self.assertEqual (solutions[0]['Y'].f, 9)


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    unittest.main()

