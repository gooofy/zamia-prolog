#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2016, 2017 Guenter Bartsch
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

import sys

from sqlalchemy import Column, Integer, String, Text, Unicode, UnicodeText, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from nltools import misc

Base = declarative_base()

class ORMClause(Base):

    __tablename__ = 'clauses'

    id                = Column(Integer, primary_key=True)

    module            = Column(String(255), index=True)
    head              = Column(String(255), index=True)
    arity             = Column(Integer, index=True) 
    prolog            = Column(Text)
  
class ORMPredicateDoc(Base):

    __tablename__ = 'predicate_docs'

    module            = Column(String(255), index=True)
    name              = Column(String(255), primary_key=True)

    doc               = Column(UnicodeText)

class ORMGensymNum(Base):

    __tablename__ = 'gensym_nums'

    root              = Column(String(255), primary_key=True)
    current_num       = Column(Integer)

