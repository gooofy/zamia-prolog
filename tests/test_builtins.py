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

UNITTEST_MODULE = 'unittests'

class TestBuiltins (unittest.TestCase):

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
    def test_hanoi1(self):

        self.parser.compile_file('samples/hanoi1.pl', UNITTEST_MODULE, self.db)

        clause = self.parser.parse_line_clause_body('move(3,left,right,center)')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause)
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 1)

    # @unittest.skip("temporarily disabled")
    def test_lists(self):

        clause = self.parser.parse_line_clause_body('X is []')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions[0]['X'].l), 0)

        clause = self.parser.parse_line_clause_body('L is [1,2,3,4], X is list_sum(L), Y is list_max(L), Z is list_min(L), W is list_avg(L), V is list_len(L)')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions[0]['L'].l), 4)
        self.assertEqual (solutions[0]['L'].l[3].f, 4.0)

        self.assertEqual (solutions[0]['X'].f, 10.0)
        self.assertEqual (solutions[0]['Y'].f, 4.0)
        self.assertEqual (solutions[0]['Z'].f, 1.0)
        self.assertEqual (solutions[0]['W'].f, 2.5)
        self.assertEqual (solutions[0]['V'].f, 4.0)

        clause = self.parser.parse_line_clause_body('L is [1,2,3,4], list_contains(L, 2).')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions), 1)

        clause = self.parser.parse_line_clause_body('L is [1,2,3,4], list_contains(L, 23).')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions), 0)

        clause = self.parser.parse_line_clause_body('X is [1,2,3,4], list_nth(1, X, E).')
        solutions = self.rt.search(clause)
        self.assertEqual (solutions[0]['E'].f, 2)

        clause = self.parser.parse_line_clause_body('X is [1,2,3,4], list_slice(1, 3, X, E).')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions[0]['E'].l), 2)
        self.assertEqual (solutions[0]['E'].l[0].f, 2.0)
        self.assertEqual (solutions[0]['E'].l[1].f, 3.0)

        clause = self.parser.parse_line_clause_body('X is [1,2,3,4], list_append(X, 5).')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions[0]['X'].l), 5)
        self.assertEqual (solutions[0]['X'].l[4].f, 5.0)

        clause = self.parser.parse_line_clause_body('X is ["1","2","3","4"], list_str_join("@", X, Y).')
        solutions = self.rt.search(clause)
        self.assertEqual (solutions[0]['Y'].s, "1@2@3@4")

    # @unittest.skip("temporarily disabled")
    def test_strings(self):

        clause = self.parser.parse_line_clause_body('X is \'bar\', S is format_str(\'test %d %s foo\', 42, X)')
        solutions = self.rt.search(clause)
        self.assertEqual (solutions[0]['S'].s, 'test 42 bar foo')

        clause = self.parser.parse_line_clause_body('X is \'foobar\', sub_string(X, 0, 2, _, Y)')
        solutions = self.rt.search(clause)
        self.assertEqual (solutions[0]['Y'].s, 'fo')

        clause = self.parser.parse_line_clause_body('atom_chars(foo, X), atom_chars(Y, "bar").')
        solutions = self.rt.search(clause)
        self.assertEqual (solutions[0]['X'].s, 'foo')
        self.assertEqual (solutions[0]['Y'].name, 'bar')

    # @unittest.skip("temporarily disabled")
    def test_date_time(self):

        clause = self.parser.parse_line_clause_body('get_time(T)')
        solutions = self.rt.search(clause)
        self.assertGreater (solutions[0]['T'].s, '2017-04-30T23:39:29.092271')

        clause = self.parser.parse_line_clause_body('date_time_stamp(date(2017,2,14,1,2,3,\'local\'), TS), stamp_date_time(TS, date(Y,M,D,H,Mn,S,\'local\'))')
        solutions = self.rt.search(clause)
        self.assertEqual (solutions[0]['Y'].f,  2017)
        self.assertEqual (solutions[0]['M'].f,  2)
        self.assertEqual (solutions[0]['D'].f,  14)
        self.assertEqual (solutions[0]['H'].f,  1)
        self.assertEqual (solutions[0]['Mn'].f, 2)
        self.assertEqual (solutions[0]['S'].f,  3)

        clause = self.parser.parse_line_clause_body('date_time_stamp(date(2017,2,14,1,2,3,\'Europe/Berlin\'), TS)')
        solutions = self.rt.search(clause)
        self.assertEqual (solutions[0]['TS'].s, '2017-02-14T01:02:03+01:00')

    # @unittest.skip("temporarily disabled")
    def test_arith(self):
        clause = self.parser.parse_line_clause_body('X is -23')
        solutions = self.rt.search(clause)
        self.assertEqual (solutions[0]['X'].f, -23)

        clause = self.parser.parse_line_clause_body('X is +42')
        solutions = self.rt.search(clause)
        self.assertEqual (solutions[0]['X'].f, 42)

        clause = self.parser.parse_line_clause_body('X is 19 + 23')
        solutions = self.rt.search(clause)
        self.assertEqual (solutions[0]['X'].f, 42)

        clause = self.parser.parse_line_clause_body('X is 61 - 19')
        solutions = self.rt.search(clause)
        self.assertEqual (solutions[0]['X'].f, 42)

        clause = self.parser.parse_line_clause_body('X is 6*7')
        solutions = self.rt.search(clause)
        self.assertEqual (solutions[0]['X'].f, 42)

        clause = self.parser.parse_line_clause_body('X is 1764 / 42')
        solutions = self.rt.search(clause)
        self.assertEqual (solutions[0]['X'].f, 42)

        clause = self.parser.parse_line_clause_body('X is 85 mod 43')
        solutions = self.rt.search(clause)
        self.assertEqual (solutions[0]['X'].f, 42)

    # @unittest.skip("temporarily disabled")
    def test_comp(self):

        clause = self.parser.parse_line_clause_body('3>1')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions), 1)
        clause = self.parser.parse_line_clause_body('1>1')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions), 0)

        clause = self.parser.parse_line_clause_body('3<1')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions), 0)
        clause = self.parser.parse_line_clause_body('1<1')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions), 0)

        clause = self.parser.parse_line_clause_body('3=<1')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions), 0)
        clause = self.parser.parse_line_clause_body('1=<1')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions), 1)

        clause = self.parser.parse_line_clause_body('3>=1')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions), 1)
        clause = self.parser.parse_line_clause_body('1>=1')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions), 1)

        clause = self.parser.parse_line_clause_body('3\\=1')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions), 1)
        clause = self.parser.parse_line_clause_body('1\\=1')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions), 0)

        clause = self.parser.parse_line_clause_body('3=1')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions), 0)
        clause = self.parser.parse_line_clause_body('1=1')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions), 1)

    # @unittest.skip("temporarily disabled")
    def test_dicts(self):

        clause = self.parser.parse_line_clause_body('dict_put(U, foo, 42), X is U, dict_put(X, bar, 23)')
        solutions = self.rt.search(clause)
        self.assertEqual (len(solutions[0]['U'].d), 1)
        self.assertEqual (len(solutions[0]['X'].d), 2)


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    unittest.main()

