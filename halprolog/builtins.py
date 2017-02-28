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
# basic HAL-Prolog builtins
#

import sys
import datetime
import dateutil.parser
import time
import pytz # $ pip install pytz
from tzlocal import get_localzone # $ pip install tzlocal

from logic import *
from errors import *

def builtin_cmp_op(g, op, rt):

    pred = g.terms[g.inx]
    args = pred.args
    if len(args) != 2:
        raise PrologRuntimeError('cmp_op: 2 args expected.')

    a = rt.prolog_get_float(args[0], g.env)
    b = rt.prolog_get_float(args[1], g.env)

    res = op(a,b)

    if rt.trace:
        logging.info("builtin_cmp_op called, a=%s, b=%s, res=%s" % (a, b, res))

    return res

def builtin_larger(g, rt):           return builtin_cmp_op(g, lambda a,b: a>b  ,rt)
def builtin_smaller(g, rt):          return builtin_cmp_op(g, lambda a,b: a<b  ,rt)
def builtin_smaller_or_equal(g, rt): return builtin_cmp_op(g, lambda a,b: a<=b ,rt)
def builtin_larger_or_equal(g, rt):  return builtin_cmp_op(g, lambda a,b: a>=b ,rt)
def builtin_non_equal(g, rt):        return builtin_cmp_op(g, lambda a,b: a!=b ,rt)
def builtin_equal(g, rt):            return builtin_cmp_op(g, lambda a,b: a==b ,rt)

def builtin_date_time_stamp(g, rt):

    # logging.debug( "builtin_date_time_stamp called, g: %s" % g)
    rt._trace ('CALLED BUILTIN date_time_stamp', g)

    pred = g.terms[g.inx]
    args = pred.args
    if len(args) != 2:
        raise PrologRuntimeError('date_time_stamp: 2 args expected.')

    if not isinstance(args[0], Predicate) or not args[0].name == 'date' or len(args[0].args) != 7:
        raise PrologRuntimeError('date_time_stamp: arg0: date structure expected.')

    arg_Y   = rt.prolog_get_int(args[0].args[0], g.env)
    arg_M   = rt.prolog_get_int(args[0].args[1], g.env)
    arg_D   = rt.prolog_get_int(args[0].args[2], g.env)
    arg_H   = rt.prolog_get_int(args[0].args[3], g.env)
    arg_Mn  = rt.prolog_get_int(args[0].args[4], g.env)
    arg_S   = rt.prolog_get_int(args[0].args[5], g.env)
    arg_TZ  = rt.prolog_get_string(args[0].args[6], g.env)

    #if pe.trace:
    #    print "BUILTIN date_time_stamp called, Y=%s M=%s D=%s H=%s Mn=%s S=%s TZ=%s" % ( str(arg_Y), str(arg_M), str(arg_D), str(arg_H), str(arg_Mn), str(arg_S), str(arg_TZ))

    tz = get_localzone() if arg_TZ == 'local' else pytz.timezone(arg_TZ)

    if not isinstance(args[1], Variable):
        raise PrologRuntimeError('date_time_stamp: arg1: variable expected.')

    v = g.env.get(args[1].name)
    if v:
        raise PrologRuntimeError('date_time_stamp: arg1: variable already bound.')
    
    dt = datetime.datetime(arg_Y, arg_M, arg_D, arg_H, arg_Mn, arg_S, tzinfo=tz)
    g.env[args[1].name] = NumberLiteral(time.mktime(dt.timetuple()))

    return True

def builtin_get_time(g, rt):

    rt._trace ('CALLED BUILTIN get_time', g)

    pred = g.terms[g.inx]
    args = pred.args
    if len(args) != 1:
        raise PrologRuntimeError('get_time: 1 arg expected.')

    arg_T   = rt.prolog_get_variable(args[0], g.env)

    dt = datetime.datetime.now()
    g.env[arg_T] = NumberLiteral(time.mktime(dt.timetuple()))

    return True

def builtin_stamp_date_time(g, rt):

    rt._trace ('CALLED BUILTIN stamp_date_time', g)

    pred = g.terms[g.inx]

    args = pred.args
    if len(args) != 2:
        raise PrologRuntimeError('stamp_date_time: 2 args expected.')

    if not isinstance(args[1], Predicate) or not args[1].name == 'date' or len(args[1].args) != 7:
        raise PrologRuntimeError('stamp_date_time: arg1: date structure expected.')

    try:
        arg_Y   = rt.prolog_get_variable(args[1].args[0], g.env)
        arg_M   = rt.prolog_get_variable(args[1].args[1], g.env)
        arg_D   = rt.prolog_get_variable(args[1].args[2], g.env)
        arg_H   = rt.prolog_get_variable(args[1].args[3], g.env)
        arg_Mn  = rt.prolog_get_variable(args[1].args[4], g.env)
        arg_S   = rt.prolog_get_variable(args[1].args[5], g.env)
        arg_TZ  = rt.prolog_get_string(args[1].args[6], g.env)

        tz = get_localzone() if arg_TZ == 'local' else pytz.timezone(arg_TZ)

        arg_TS  = rt.prolog_get_float(args[0], g.env)

        dt = datetime.datetime.fromtimestamp(arg_TS, tz)

        g.env[arg_Y]  = NumberLiteral(dt.year)
        g.env[arg_M]  = NumberLiteral(dt.month)
        g.env[arg_D]  = NumberLiteral(dt.day)
        g.env[arg_H]  = NumberLiteral(dt.hour)
        g.env[arg_Mn] = NumberLiteral(dt.minute)
        g.env[arg_S]  = NumberLiteral(dt.second)

    except PrologRuntimeError:
        return False

    return True

def builtin_sub_string(g, rt):

    rt._trace ('CALLED BUILTIN sub_string', g)

    pred = g.terms[g.inx]
    args = pred.args
    if len(args) != 5:
        raise PrologRuntimeError('sub_string: 5 args expected.')

    arg_String    = rt.prolog_get_string(args[0], g.env)
    arg_Before    = rt.prolog_eval(args[1], g.env)
    arg_Length    = rt.prolog_eval(args[2], g.env) 
    arg_After     = rt.prolog_eval(args[3], g.env)  
    arg_SubString = rt.prolog_eval(args[4], g.env)  

    # FIXME: implement other variants
    if arg_Before:
        if not isinstance (arg_Before, NumberLiteral):
            raise PrologRuntimeError('sub_string: arg_Before: Number expected, %s found instead.' % arg_Before.__class__)
        before = int(arg_Before.f)
        
        if arg_Length:

            if not isinstance (arg_Length, NumberLiteral):
                raise PrologRuntimeError('sub_string: arg_Length: Number expected, %s found instead.' % arg_Length.__class__)
            length = int(arg_Length.f)

            if arg_After:
                raise PrologRuntimeError('sub_string: FIXME: arg_After required to be a variable for now.')
            else:

                var_After = rt.prolog_get_variable(args[3], g.env)
                if var_After != '_':
                    g.env[var_After] = NumberLiteral(len(arg_String) - before - length)

                if arg_SubString:
                    raise PrologRuntimeError('sub_string: FIXME: arg_SubString required to be a variable for now.')
                else:
                    var_SubString = rt.prolog_get_variable(args[4], g.env)

                    if var_SubString != '_':
                        g.env[var_SubString] = StringLiteral(arg_String[before:before + length])

        else:
            raise PrologRuntimeError('sub_string: FIXME: arg_Length required to be a literal for now.')
    else:
        raise PrologRuntimeError('sub_string: FIXME: arg_Before required to be a literal for now.')
        
    return True

def builtin_write(g, rt):

    rt._trace ('CALLED BUILTIN write', g)

    term = g.terms[g.inx].args[0]

    t = rt.prolog_eval(term, g.env)

    if isinstance (t, StringLiteral):
        sys.stdout.write(t.s)
    else:
        sys.stdout.write(unicode(t))
        
    return True
 
def builtin_nl(g, rt):

    rt._trace ('CALLED BUILTIN nl', g)

    sys.stdout.write('\n')

    return True

def builtin_list_contains(g, rt):

    rt._trace_fn ('CALLED BUILTIN list_contains', g)

    pred = g.terms[g.inx]

    args = pred.args
    if len(args) != 2:
        raise PrologRuntimeError('list_contains: 2 args expected.')

    arg_list   = rt.prolog_get_list (args[0], g.env)
    arg_needle = rt.prolog_eval(args[1], g.env)

    for o in arg_list.l:
        if o == arg_needle:
            return True

    return False

#
# functions
#

def builtin_format_str(pred, env, rt):

    rt._trace_fn ('CALLED FUNCTION format_str', env)

    args  = pred.args
    arg_F = rt.prolog_get_string(args[0], env)

    if len(args)>1:
        
        a = map(lambda x: rt.prolog_get_literal(x, env), args[1:])

        f_str = arg_F % tuple(a)

    else:

        f_str = arg_F

    return StringLiteral(f_str)

def builtin_isoformat(pred, env, rt):

    rt._trace_fn ('CALLED FUNCTION isoformat', env)

    args = pred.args
    if len(args) != 2:
        raise PrologRuntimeError('isoformat: 2 args expected.')

    arg_TS  = rt.prolog_get_float (args[0], env)
    arg_TZ  = rt.prolog_get_string(args[1], env)

    tz = get_localzone() if arg_TZ == 'local' else pytz.timezone(arg_TZ)

    dt = datetime.datetime.fromtimestamp(arg_TS, tz)

    return StringLiteral(dt.isoformat())

def _builtin_list_lambda (pred, env, rt, l):

    args = pred.args
    if len(args) != 1:
        raise PrologRuntimeError('list builtin fn: 1 arg expected.')

    arg_list = rt.prolog_get_list (args[0], env)

    res = reduce(l, arg_list.l)
    return res, arg_list.l
    # if isinstance(res, (int, float)):
    #     return NumberLiteral(res)
    # else:
    #     return StringLiteral(unicode(res))

def builtin_list_max(pred, env, rt):

    rt._trace_fn ('CALLED FUNCTION list_max', env)

    return _builtin_list_lambda (pred, env, rt, lambda x, y: x if x > y else y)[0]

def builtin_list_min(pred, env, rt):

    rt._trace_fn ('CALLED FUNCTION list_min', env)

    return _builtin_list_lambda (pred, env, rt, lambda x, y: x if x < y else y)[0]

def builtin_list_sum(pred, env, rt):

    rt._trace_fn ('CALLED FUNCTION list_sum', env)

    return _builtin_list_lambda (pred, env, rt, lambda x, y: x + y)[0]

def builtin_list_avg(pred, env, rt):

    rt._trace_fn ('CALLED FUNCTION list_avg', env)

    l_sum, l = _builtin_list_lambda (pred, env, rt, lambda x, y: x + y)

    assert len(l)>0
    return l_sum / NumberLiteral(float(len(l)))

