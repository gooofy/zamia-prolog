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
    def test_hanoi2(self):

        global recorded_moves

        self.db.clear_module('unittests')

        self.parser.compile_file('samples/hanoi2.pl', 'unittests', self.db)

        clause = self.parser.parse_line_clause_body('move(3,left,right,center)')
        logging.debug('clause: %s' % clause)

        # register our custom builtin
        recorded_moves = []
        self.rt.register_builtin('record_move', record_move)

        solutions = self.rt.search(clause)
        logging.debug('solutions: %s' % repr(solutions))
        self.assertEqual (len(solutions), 1)

        self.assertEqual (len(recorded_moves), 7)


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    unittest.main()

