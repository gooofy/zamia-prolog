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
# Zamia-Prolog 
# ------------
#
# Zamia-Prolog grammar
#
# program       ::= { clause }
#
# clause        ::= relation [ ':-' clause_body ] '.' 
#
# relation      ::= name [ '(' term { ',' term } ')' ]
#
# clause_body   ::= subgoals { ';' subgoals }
#
# subgoals      ::= subgoal { ',' subgoal }
#
# subgoal       ::= ( term | conditional )
#
# conditional   ::= 'if' term 'then' subgoals [ 'else' subgoals ] 'endif'
#
# term          ::= add-term { rel-op add-term }
#
# rel-op        ::= '=' | '\=' | '<' | '>' | '=<' | '>=' | 'is' 
#
# add-term      ::= mul-term { add-op mul-term } 
#
# add-op        ::= '+' | '-' 
#
# mul-term      ::= unary-term  { mul-op unary-term } 
#
# mul-op        ::= '*' | '/' | 'div' | 'mod'
#
# unary-term    ::= [ unary-op ] primary-term  
#
# unary-op      ::= '+' | '-' 
#
# primary-term  ::= ( variable | number | string | list | relation | '(' term { ',' term } ')' | '!' )
#
# list          ::= '[' [ primary-term ] ( { ',' primary-term } | '|' primary-term ) ']'
#

import os
import sys
import logging
import codecs
import re

from copy                import copy
from StringIO            import StringIO

from zamiaprolog.logic   import *
from zamiaprolog.errors  import *
from zamiaprolog.runtime import PrologRuntime
from nltools.tokenizer   import tokenize

# lexer

REL_OP   = set ([u'=', u'\\=', u'<', u'>', u'=<', u'>=', u'is']) 
ADD_OP   = set ([u'+', u'-'])
MUL_OP   = set ([u'*', u'/', u'div', u'mod'])
UNARY_OP = set ([u'+', u'-'])

NAME_CHARS = set([u'a',u'b',u'c',u'd',u'e',u'f',u'g',u'h',u'i',u'j',u'k',u'l',u'm',u'n',u'o',u'p',u'q',u'r',u's',u't',u'u',u'v',u'w',u'x',u'y',u'z',
                  u'A',u'B',u'C',u'D',u'E',u'F',u'G',u'H',u'I',u'J',u'K',u'L',u'M',u'N',u'O',u'P',u'Q',u'R',u'S',u'T',u'U',u'V',u'W',u'X',u'Y',u'Z',
                  u'_',u'0',u'1',u'2',u'3',u'4',u'5',u'6',u'7',u'8',u'9'])

NAME_CHARS_EXTENDED = NAME_CHARS | set([':','|'])

SIGN_CHARS = set([u'=',u'<',u'>',u'+',u'-',u'*',u'/',u'\\'])

SYM_NONE       =  0
SYM_EOF        =  1
SYM_STRING     =  2   # 'abc'
SYM_NAME       =  3   # abc aWord =< is div + 
SYM_VARIABLE   =  4   # X Variable _Variable _
SYM_NUMBER     =  5  

SYM_IMPL       = 10   # :-
SYM_LPAREN     = 11   # (
SYM_RPAREN     = 12   # )
SYM_COMMA      = 13   # ,
SYM_PERIOD     = 14   # .
SYM_SEMICOLON  = 15   # ;
SYM_COLON      = 17   # :
SYM_LBRACKET   = 18   # [
SYM_RBRACKET   = 19   # ]
SYM_PIPE       = 20   # |
SYM_CUT        = 21   # !
SYM_IF         = 22   # if
SYM_THEN       = 23   # then
SYM_ELSE       = 24   # else
SYM_ENDIF      = 25   # endif

# structured comments
CSTATE_IDLE    = 0
CSTATE_HEADER  = 1
CSTATE_BODY    = 2

class PrologParser(object):

    def __init__(self):
        # compile-time built-in predicates
        self.directives       = {}
    
    def report_error(self, s):
        raise PrologError ("%s: error in line %d col %d: %s" % (self.prolog_fn, self.cur_line, self.cur_col, s))

    def get_location(self):
        return SourceLocation(self.prolog_fn, self.cur_line, self.cur_col)

    def next_c(self):
        self.cur_c    = unicode(self.prolog_f.read(1))
        self.cur_col += 1

        if self.cur_c == u'\n':
            self.cur_line += 1
            self.cur_col   = 1
            if (self.linecnt > 0) and (self.cur_line % 1000 == 0):
                logging.info ("%s: parsing line %6d / %6d (%3d%%)" % (self.prolog_fn, 
                                                                      self.cur_line, 
                                                                      self.linecnt, 
                                                                      self.cur_line * 100 / self.linecnt))

        # print '[', self.cur_c, ']',

    def peek_c(self):
        peek_c = unicode(self.prolog_f.read(1))
        self.prolog_f.seek(-1,1)
        return peek_c

    def is_name_char(self, c):
        if c in NAME_CHARS:
            return True

        if ord(c) >= 128:
            return True

        return False

    def is_name_char_ext(self, c):
        if c in NAME_CHARS_EXTENDED:
            return True

        if ord(c) >= 128:
            return True

        return False

    def next_sym(self):

        # whitespace, comments

        self.cstate       = CSTATE_IDLE

        while True:
            # skip whitespace
            while not (self.cur_c is None) and self.cur_c.isspace():
                self.next_c()

            if not self.cur_c:
                self.cur_sym = SYM_EOF
                return

            # skip comments
            if self.cur_c == u'%':

                comment_line = u''
                
                self.next_c()
                if self.cur_c == u'!':
                    self.cstate = CSTATE_HEADER
                    self.next_c()

                while True:
                    if not self.cur_c:
                        self.cur_sym = SYM_EOF
                        return
                    if self.cur_c == u'\n':
                        self.next_c()
                        break
                    comment_line += self.cur_c
                    self.next_c()

                if self.cstate == CSTATE_HEADER:
                    m = re.match (r"^\s*doc\s+([a-zA-Z0-9_]+)", comment_line)
                    if m:
                        self.comment_pred = m.group(1)
                        self.comment = ''
                        self.cstate = CSTATE_BODY

                elif self.cstate == CSTATE_BODY:
                    if len(self.comment)>0:
                        self.comment += '\n'
                    self.comment += comment_line.lstrip().rstrip()

            else:
                break

        #if self.comment_pred:
        #    print "COMMENT FOR %s : %s" % (self.comment_pred, self.comment)

        self.cur_str = u''

        if self.cur_c == u'\'' or self.cur_c == u'"':
            self.cur_sym = SYM_STRING
            startc = self.cur_c

            while True:
                self.next_c()

                if not self.cur_c:
                    self.report_error ("Unterminated string literal.")
                    self.cur_sym = SYM_EOF
                    break
                if self.cur_c == u'\\':
                    self.next_c()
                    self.cur_str += self.cur_c
                    self.next_c()

                if self.cur_c == startc:
                    self.next_c()
                    break

                self.cur_str += self.cur_c

        elif self.cur_c.isdigit():
            self.cur_sym = SYM_NUMBER

            while True:
                self.cur_str += self.cur_c
                self.next_c()
                if self.cur_c == '.' and not self.peek_c().isdigit():
                    break

                if not self.cur_c or (not self.cur_c.isdigit() and self.cur_c != '.'):
                    break

        elif self.is_name_char(self.cur_c):
            self.cur_sym = SYM_VARIABLE if self.cur_c == u'_' or self.cur_c.isupper() else SYM_NAME

            while True:
                self.cur_str += self.cur_c
                self.next_c()
                if not self.cur_c or not self.is_name_char_ext(self.cur_c):
                    break

            # keywords

            if self.cur_str == 'if':
                self.cur_sym = SYM_IF
            elif self.cur_str == 'then':
                self.cur_sym = SYM_THEN
            elif self.cur_str == 'else':
                self.cur_sym = SYM_ELSE
            elif self.cur_str == 'endif':
                self.cur_sym = SYM_ENDIF
        elif self.cur_c in SIGN_CHARS:
            self.cur_sym = SYM_NAME

            while True:
                self.cur_str += self.cur_c
                self.next_c()
                if not self.cur_c or not (self.cur_c in SIGN_CHARS):
                    break

        elif self.cur_c == u':':
            self.next_c()

            if self.cur_c == u'-':
                self.next_c()
                self.cur_sym = SYM_IMPL
            else:
                self.cur_sym = SYM_COLON

        elif self.cur_c == u'(':
            self.cur_sym = SYM_LPAREN
            self.next_c()
        elif self.cur_c == u')':
            self.cur_sym = SYM_RPAREN
            self.next_c()

        elif self.cur_c == u',':
            self.cur_sym = SYM_COMMA
            self.next_c()

        elif self.cur_c == u'.':
            self.cur_sym = SYM_PERIOD
            self.next_c()

        elif self.cur_c == u';':
            self.cur_sym = SYM_SEMICOLON
            self.next_c()

        elif self.cur_c == u'[':
            self.cur_sym = SYM_LBRACKET
            self.next_c()

        elif self.cur_c == u']':
            self.cur_sym = SYM_RBRACKET
            self.next_c()

        elif self.cur_c == u'|':
            self.cur_sym = SYM_PIPE
            self.next_c()

        elif self.cur_c == u'!':
            self.cur_sym = SYM_NAME
            self.cur_str = 'cut'
            self.next_c()

        else:
            self.report_error ("Illegal character: " + repr(self.cur_c))

        #print "[%2d]" % self.cur_sym,


    #
    # parser starts here
    #

    def parse_list(self):

        res = ListLiteral([])

        if self.cur_sym != SYM_RBRACKET:
    
            res.l.append(self.primary_term())

            # FIXME: implement proper head/tail mechanics

            if self.cur_sym == SYM_PIPE:
                self.next_sym()
                res.l.append(self.primary_term())

            else:

                while (self.cur_sym == SYM_COMMA):
                    self.next_sym()
                    res.l.append(self.primary_term())

        if self.cur_sym != SYM_RBRACKET:
            self.report_error ("list: ] expected.")
        self.next_sym()

        return res

    def primary_term(self):

        res = None

        if self.cur_sym == SYM_VARIABLE:
            res = Variable (self.cur_str)
            self.next_sym()

        elif self.cur_sym == SYM_NUMBER:
            res = NumberLiteral (float(self.cur_str))
            self.next_sym()

        elif self.cur_sym == SYM_STRING:
            res = StringLiteral (self.cur_str)
            self.next_sym()

        elif self.cur_sym == SYM_NAME:
            res = self.relation()

        elif self.cur_sym == SYM_LPAREN:
            self.next_sym()
            res = self.term()

            while (self.cur_sym == SYM_COMMA):
                self.next_sym()
                if not isinstance(res, list):
                    res = [res]
                res.append(self.term())

            if self.cur_sym != SYM_RPAREN:
                self.report_error ("primary term: ) expected.")
            self.next_sym()

        elif self.cur_sym == SYM_LBRACKET:
            self.next_sym()
            res = self.parse_list()

        else:
            self.report_error ("primary term: variable / number / string / name / ( expected.")

        # logging.debug ('primary_term: %s' % str(res))

        return res

    def unary_term(self):

        o = None

        if self.cur_sym == SYM_NAME and self.cur_str in UNARY_OP:
            o = self.cur_str
            self.next_sym()

        res = self.primary_term()
        if o:
            if not isinstance(res, list):
                res = [res]
            
            res = Predicate (o, res)

        return res


    def mul_term(self):

        args = []
        ops  = []

        args.append(self.unary_term())

        while self.cur_sym == SYM_NAME and self.cur_str in MUL_OP:
            ops.append(self.cur_str)
            self.next_sym()
            args.append(self.unary_term())

        res = None
        while len(args)>0:
            arg = args.pop()
            if not res:
                res = arg
            else:
                res = Predicate (o, [arg, res])

            if len(ops)>0:
                o = ops.pop()

        # logging.debug ('mul_term: ' + str(res))

        return res


    def add_term(self):

        args = []
        ops  = []

        args.append(self.mul_term())

        while self.cur_sym == SYM_NAME and self.cur_str in ADD_OP:
            ops.append(self.cur_str)
            self.next_sym()
            args.append(self.mul_term())

        res = None
        while len(args)>0:
            arg = args.pop()
            if not res:
                res = arg
            else:
                res = Predicate (o, [arg, res])

            if len(ops)>0:
                o = ops.pop()

        # logging.debug ('add_term: ' + str(res))

        return res

    def term(self):
       
        args = []
        ops  = []

        args.append(self.add_term())

        while self.cur_sym == SYM_NAME and self.cur_str in REL_OP:
            ops.append(self.cur_str)
            self.next_sym()
            args.append(self.add_term())

        res = None
        while len(args)>0:
            arg = args.pop()
            if not res:
                res = arg
            else:
                res = Predicate (o, [arg, res])

            if len(ops)>0:
                o = ops.pop()

        # logging.debug ('term: ' + str(res))

        return res


    def relation(self):

        if self.cur_sym != SYM_NAME:
            self.report_error ("Name expected.")
        name = self.cur_str
        self.next_sym()

        args = None

        if self.cur_sym == SYM_LPAREN:
            self.next_sym()

            args = []

            while True:

                args.append(self.term())

                if self.cur_sym != SYM_COMMA:
                    break
                self.next_sym()

            if self.cur_sym != SYM_RPAREN:
                self.report_error ("relation: ) expected.")
            self.next_sym()

        return Predicate (name, args)

    def subgoal(self):

        if self.cur_sym == SYM_IF:

            self.next_sym()

            c = self.term()

            if self.cur_sym != SYM_THEN:
                self.report_error ("subgoal: then expected.")
            self.next_sym()

            t = self.subgoals()
            t = Predicate ('and', [c, t])

            if self.cur_sym == SYM_ELSE:
                self.next_sym()
                e  = self.subgoals()
                nc = Predicate ('not', [c])
                e  = Predicate ('and', [nc, e])
            else:
                e = Predicate ('true')

            if self.cur_sym != SYM_ENDIF:
                self.report_error ("subgoal: endif expected.")
            self.next_sym()

            return [ Predicate ('or', [t, e]) ]

        else:
            return [ self.term() ]
    def subgoals(self):

        res = self.subgoal()

        while self.cur_sym == SYM_COMMA:
            self.next_sym()

            t2 = self.subgoal()
            res.extend(t2)

        if len(res) == 1:
            return res[0]
        
        return Predicate ('and', res)

    def clause_body(self):

        res = [ self.subgoals() ]

        while self.cur_sym == SYM_SEMICOLON:
            self.next_sym()

            sg2 = self.subgoals()
            res.append(sg2)

        if len(res) == 1:
            return res[0]

        return Predicate ('or', res)

    def clause(self, db):

        res = []

        loc = self.get_location()

        head = self.relation()

        if self.cur_sym == SYM_IMPL:
            self.next_sym()

            body = self.clause_body()

            c = Clause (head, body, location=loc)

        else:
            c = Clause (head, location=loc)

        if self.cur_sym != SYM_PERIOD:
            self.report_error ("clause: . expected.")
        self.next_sym()

        # compiler directive?

        if c.head.name in self.directives:
            f, user_data = self.directives[c.head.name]
            f(db, self.module_name, c, user_data)

        else:
            res.append(c)


        # logging.debug ('clause: ' + str(res))

        return res

    #
    # high-level interface
    #

    def start (self, prolog_f, prolog_fn, linecnt = 1, module_name = None):

        self.cur_c        = u' '
        self.cur_sym      = SYM_NONE
        self.cur_str      = u''
        self.cur_line     = 1
        self.cur_col      = 1
        self.prolog_f     = prolog_f
        self.prolog_fn    = prolog_fn
        self.linecnt      = linecnt
        self.module_name  = module_name

        self.cstate       = CSTATE_IDLE
        self.comment_pred = None
        self.comment      = u''

        self.next_c()
        self.next_sym()

    def parse_line_clause_body (self, line):

        self.start (StringIO(line), '<str>')
        body = self.clause_body()

        return Clause (None, body, location=self.get_location())

    def parse_line_clauses (self, line):

        self.start (StringIO(line), '<str>')
        return self.clause(None)

    def register_directive(self, name, f, user_data):
        self.directives[name] = (f, user_data)

    def clear_module (self, module_name, db):
        db.clear_module(module_name)

    def compile_file (self, filename, module_name, db, clear_module=False):

        # quick source line count for progress output below

        self.linecnt = 1
        with codecs.open(filename, encoding='utf-8', errors='ignore', mode='r') as f:
            while f.readline():
                self.linecnt += 1
        logging.info("%s: %d lines." % (filename, self.linecnt))

        # remove old predicates of this module from db
        if clear_module:
            self.clear_module (module_name, db)

        # actual parsing starts here

        with codecs.open(filename, encoding='utf-8', errors='ignore', mode='r') as f:
            self.start(f, filename, module_name=module_name)

            while self.cur_sym != SYM_EOF:
                clauses = self.clause(db)

                for clause in clauses:
                    logging.debug(u"%7d / %7d (%3d%%) > %s" % (self.cur_line, self.linecnt, self.cur_line * 100 / self.linecnt, unicode(clause)))

                    db.store (module_name, clause)

                if self.comment_pred:

                    db.store_doc (module_name, self.comment_pred, self.comment)

                    self.comment_pred = None
                    self.comment = ''

        db.commit()

        logging.info("Compilation succeeded.")

