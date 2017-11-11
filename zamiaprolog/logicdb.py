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
import sys
import logging
import time

from copy           import deepcopy, copy
from sqlalchemy     import create_engine
from sqlalchemy.orm import sessionmaker
from six            import python_2_unicode_compatible, text_type
from zamiaprolog    import model

from zamiaprolog.logic import *
from nltools.misc      import limit_str

class LogicDB(object):

    def __init__(self, db_url, echo=False):

        self.engine  = create_engine(db_url, echo=echo)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        model.Base.metadata.create_all(self.engine)
        self.cache = {}

    def commit(self):
        logging.debug("commit.")
        self.session.commit()

    def close (self, do_commit=True):
        if do_commit:
            self.commit()
        self.session.close()

    def clear_module(self, module, commit=True):

        logging.info("Clearing %s ..." % module)
        self.session.query(model.ORMClause).filter(model.ORMClause.module==module).delete()
        self.session.query(model.ORMPredicateDoc).filter(model.ORMPredicateDoc.module==module).delete()
        logging.info("Clearing %s ... done." % module)

        if commit:
            self.commit()
        self.invalidate_cache()

    def clear_all_modules(self, commit=True):

        logging.info("Clearing all modules ...")
        self.session.query(model.ORMClause).delete()
        self.session.query(model.ORMPredicateDoc).delete()
        logging.info("Clearing all modules ... done.")
        
        if commit:
            self.commit()
        self.invalidate_cache()

    def store (self, module, clause):

        ormc = model.ORMClause(module    = module,
                               arity     = len(clause.head.args), 
                               head      = clause.head.name, 
                               prolog    = prolog_to_json(clause))

        # print text_type(clause)

        self.session.add(ormc)
        self.invalidate_cache(clause.head.name)
      
    def invalidate_cache(self, name=None):
        if name and name in self.cache:
            del self.cache[name]
        else:
            self.cache = {}

    def store_doc (self, module, name, doc):

        ormd = model.ORMPredicateDoc(module = module,
                                     name   = name,
                                     doc    = doc)
        self.session.add(ormd)

    # use arity=-1 to disable filtering
    def lookup (self, name, arity, overlay=None, sf=None):

        ts_start = time.time()

        # if name == 'lang':
        #     import pdb; pdb.set_trace()

        # DB caching

        if name in self.cache:
            res = copy(self.cache[name])

        else:
            res = []

            for ormc in self.session.query(model.ORMClause).filter(model.ORMClause.head==name).order_by(model.ORMClause.id).all():

                res.append (json_to_prolog(ormc.prolog))

            self.cache[name] = copy(res)
       
        if overlay:
            res = overlay.do_filter(name, res)

        if arity<0:
            return res

        res2 = []
        for clause in res:
    
            if len(clause.head.args) != arity:
                continue

            match = True
            if sf:
                for i in sf:
                    ca = sf[i]
                    a  = clause.head.args[i]
                    
                    if not isinstance(a, Predicate):
                        continue
                    if (a.name != ca) or (len(a.args) !=0):
                        # logging.info('no match: %s vs %s %s' % (repr(ca), repr(a), text_type(clause)))
                        match=False
                        break
            if not match:
                continue
            res2.append(clause)

        ts_delay = time.time() - ts_start
        # logging.debug (u'db lookup for %s/%d took %fs' % (name, arity, ts_delay))

        return res2

@python_2_unicode_compatible
class LogicDBOverlay(object):

    def __init__(self):

        self.d_assertz   = {}
        self.d_retracted = {}

    def clone(self):
        clone = LogicDBOverlay()

        for name in self.d_retracted:
            for c in self.d_retracted[name]:
                clone.retract(c)

        for name in self.d_assertz:
            for c in self.d_assertz[name]:
                clone.assertz(c)

        return clone

    def assertz (self, clause):

        name = clause.head.name

        if name in self.d_assertz:
            self.d_assertz[name].append(clause)
        else:
            self.d_assertz[name] = [clause]

    def _match_p (self, p1, p2):

        """ extremely simplified variant of full-blown unification - just enough to get basic retract/1 working """

        if isinstance (p1, Variable):
            return True

        if isinstance (p2, Variable):
            return True

        elif isinstance (p1, Literal):
            return p1 == p2

        elif p1.name != p2.name:
            return False

        elif len(p1.args) != len(p2.args): 
            return False

        else:
            for i in range(len(p1.args)):
                if not self._match_p(p1.args[i], p2.args[i]):
                    return False

        return True


    def retract (self, p):
        name = p.name

        if name in self.d_assertz:
            l = []
            for c in self.d_assertz[name]:
                if not self._match_p(p, c.head):
                    l.append(c)
            self.d_assertz[name] = l

        if name in self.d_retracted:
            self.d_retracted[name].append(p)
        else:
            self.d_retracted[name] = [p]

    def do_filter (self, name, res):

        if name in self.d_retracted:
            res2 = []
            for clause in res:
                for p in self.d_retracted[name]:
                    if not self._match_p(clause.head, p):
                        res2.append(clause)
            res = res2

        # append overlay clauses

        if name in self.d_assertz:
            for clause in self.d_assertz[name]:
                res.append(clause)

        return res

    def log_trace (self, indent):
        for k in sorted(self.d_assertz):
            for clause in self.d_assertz[k]:
                logging.info(u"%s   [O] %s" % (indent, limit_str(text_type(clause), 100)))
        # FIXME: log retracted clauses?

    def __str__ (self):
        res = u'DBOvl('
        for k in sorted(self.d_assertz):
            for clause in self.d_assertz[k]:
                res += u'+' + limit_str(text_type(clause), 40)
        for k in sorted(self.d_retracted):
            for p in self.d_retracted[k]:
                res += u'-' + limit_str(text_type(p), 40)

        res += u')'
        return res

    def __repr__(self):
        return text_type(self).encode('utf8')

    def do_apply(self, module, db, commit=True):

        to_delete = set()

        for name in self.d_retracted:
            for ormc in db.session.query(model.ORMClause).filter(model.ORMClause.head==name).all():
                clause = json_to_prolog(ormc.prolog)
                for p in self.d_retracted[name]:
                    if self._match_p(clause.head, p):
                        to_delete.add(ormc.id)

        if to_delete:
           db.session.query(model.ORMClause).filter(model.ORMClause.id.in_(list(to_delete))).delete(synchronize_session='fetch')
           db.invalidate_cache()

        for name in self.d_assertz:
            for clause in self.d_assertz[name]:
                db.store(module, clause)

        if commit:
            db.commit()


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

