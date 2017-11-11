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

UNITTEST_MODULE = 'unittests'

class TestNegation (unittest.TestCase):

    def setUp(self):

        #
        # db, store
        #

        db_url = 'sqlite:///foo.db'

        # setup compiler + environment

        self.db     = LogicDB(db_url)
        self.parser = PrologParser(self.db)
        self.rt     = PrologRuntime(self.db)

        self.db.clear_module(UNITTEST_MODULE)

        self.rt.set_trace(True)

    def tearDown(self):
        self.db.close()

    # @unittest.skip("temporarily disabled")
    def test_not_succ(self):

        clause = self.parser.parse_line_clause_body('X is 1, Y is 2, not(X is Y).')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause, {})
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 1)

    # @unittest.skip("temporarily disabled")
    def test_not_fail(self):
        clause = self.parser.parse_line_clause_body('X is 2, Y is 2, not(X is Y).')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause, {})
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 0)

    # @unittest.skip("temporarily disabled")
    def test_chancellors(self):

        self.parser.compile_file('samples/not_test.pl', UNITTEST_MODULE)

        clause = self.parser.parse_line_clause_body('was_chancellor(helmut_kohl).')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause, {})
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 1)

    # @unittest.skip("temporarily disabled")
    def test_double_negation(self):

        self.parser.compile_file('samples/not_test.pl', UNITTEST_MODULE)

        clause = self.parser.parse_line_clause_body('not(not(chancellor(helmut_kohl))).')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause, {})
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 1)

        clause = self.parser.parse_line_clause_body('not(not(chancellor(angela_merkel))).')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause, {})
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 1)

        clause = self.parser.parse_line_clause_body('not(not(chancellor(X))).')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause, {})
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 2)

    # @unittest.skip("temporarily disabled")
    def test_assertz_negation(self):

        clause = self.parser.parse_line_clause_body('assertz(foobar(a)), foobar(a), (not(foobar(b))).')
        logging.debug('clause: %s' % clause)
        solutions = self.rt.search(clause, {})
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 1)

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    unittest.main()

