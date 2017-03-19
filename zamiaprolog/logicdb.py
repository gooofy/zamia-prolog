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
# store and retrieve logic clauses to and from our relational db
#

import os
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import model

from logic  import *
from parser import PrologParser

class LogicDB(object):

    def __init__(self, db_url, echo=False):

        self.engine = create_engine(db_url, echo=echo)
        self.Session = sessionmaker(bind=self.engine)
        self.session  = self.Session()
        model.Base.metadata.create_all(self.engine)

        self.parser   = PrologParser()

    def commit(self):
        logging.info("commit.")
        self.session.commit()

    def clear_module(self, module, commit=True):

        logging.info("Clearing %s ..." % module)
        self.session.query(model.ORMClause).filter(model.ORMClause.module==module).delete()
        self.session.query(model.ORMPredicateDoc).filter(model.ORMPredicateDoc.module==module).delete()
        logging.info("Clearing %s ... done." % module)

        if commit:
            self.commit()

    def clear_all_modules(self, commit=True):

        logging.info("Clearing all modules ...")
        self.session.query(model.ORMClause).delete()
        self.session.query(model.ORMPredicateDoc).delete()
        logging.info("Clearing all modules ... done.")
        
        if commit:
            self.commit()

    def store (self, module, clause):

        ormc = model.ORMClause(module    = module,
                               arity     = len(clause.head.args), 
                               head      = clause.head.name, 
                               prolog    = unicode(clause))

        # print unicode(clause)

        self.session.add(ormc)
       
    def store_doc (self, module, name, doc):

        ormd = model.ORMPredicateDoc(module = module,
                                     name   = name,
                                     doc    = doc)
        self.session.add(ormd)

    def lookup (self, name):

        # FIXME: caching ?

        # if name in self.clauses:
        #     return self.clauses[name]

        res = []

        for ormc in self.session.query(model.ORMClause).filter(model.ORMClause.head==name).all():

            for c in self.parser.parse_line_clauses(ormc.prolog):
                res.append (c)
        
        return res

# class LogicMemDB(object):
# 
#     def __init__(self):
#         self.clauses = {}
# 
#     def store (self, clause):
#         if clause.head.name in self.clauses:
#             self.clauses[clause.head.name].append (clause)
#         else:
#             self.clauses[clause.head.name] = [clause]
#        
#     def lookup (self, name):
#         if name in self.clauses:
#             return self.clauses[name]
#         return []

