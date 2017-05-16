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
# basic Zamia-Prolog builtins
#

import sys
import datetime
import dateutil.parser
import time
import pytz # $ pip install pytz

from tzlocal import get_localzone # $ pip install tzlocal
from copy    import deepcopy

import model

from logic   import *
from errors  import *

def builtin_cmp_op(g, op, rt):

    pred = g.terms[g.inx]
    args = pred.args
    if len(args) != 2:
        raise PrologRuntimeError('cmp_op: 2 args expected.', g.location)

    a = rt.prolog_get_literal(args[0], g.env, g.location)
    b = rt.prolog_get_literal(args[1], g.env, g.location)

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

def builtin_arith_imp(g, op, rt):

    pred = g.terms[g.inx]
    args = pred.args
    if len(args) != 2:
        raise PrologRuntimeError('arith_op: 2 args expected.', g.location)

    a = rt.prolog_get_variable (args[0], g.env, g.location)
    b = rt.prolog_get_float    (args[1], g.env, g.location)

    af = g.env[a].f if a in g.env else 0.0

    res = NumberLiteral(op(af,b))

    if rt.trace:
        logging.info("builtin_arith_op called, a=%s, b=%s, res=%s" % (a, b, res))

    g.env[a] = res

    return True

def builtin_increment(g, rt):       return builtin_arith_imp(g, lambda a,b: a+b ,rt)
def builtin_decrement(g, rt):       return builtin_arith_imp(g, lambda a,b: a-b ,rt)

def builtin_date_time_stamp(g, rt):

    # logging.debug( "builtin_date_time_stamp called, g: %s" % g)
    rt._trace ('CALLED BUILTIN date_time_stamp', g)

    pred = g.terms[g.inx]
    args = pred.args
    if len(args) != 2:
        raise PrologRuntimeError('date_time_stamp: 2 args expected.', g.location)

    if not isinstance(args[0], Predicate) or not args[0].name == 'date' or len(args[0].args) != 7:
        raise PrologRuntimeError('date_time_stamp: arg0: date structure expected.', g.location)

    arg_Y   = rt.prolog_get_int(args[0].args[0], g.env, g.location)
    arg_M   = rt.prolog_get_int(args[0].args[1], g.env, g.location)
    arg_D   = rt.prolog_get_int(args[0].args[2], g.env, g.location)
    arg_H   = rt.prolog_get_int(args[0].args[3], g.env, g.location)
    arg_Mn  = rt.prolog_get_int(args[0].args[4], g.env, g.location)
    arg_S   = rt.prolog_get_int(args[0].args[5], g.env, g.location)
    arg_TZ  = rt.prolog_get_string(args[0].args[6], g.env, g.location)

    #if pe.trace:
    #    print "BUILTIN date_time_stamp called, Y=%s M=%s D=%s H=%s Mn=%s S=%s TZ=%s" % ( str(arg_Y), str(arg_M), str(arg_D), str(arg_H), str(arg_Mn), str(arg_S), str(arg_TZ))

    tz = get_localzone() if arg_TZ == 'local' else pytz.timezone(arg_TZ)

    if not isinstance(args[1], Variable):
        raise PrologRuntimeError('date_time_stamp: arg1: variable expected.', g.location)

    v = g.env.get(args[1].name)
    if v:
        raise PrologRuntimeError('date_time_stamp: arg1: variable already bound.', g.location)
    
    dt = datetime.datetime(arg_Y, arg_M, arg_D, arg_H, arg_Mn, arg_S, tzinfo=tz)
    g.env[args[1].name] = StringLiteral(dt.isoformat())

    return True

def builtin_get_time(g, rt):

    rt._trace ('CALLED BUILTIN get_time', g)

    pred = g.terms[g.inx]
    args = pred.args
    if len(args) != 1:
        raise PrologRuntimeError('get_time: 1 arg expected.', g.location)

    arg_T   = rt.prolog_get_variable(args[0], g.env, g.location)

    dt = datetime.datetime.now()
    g.env[arg_T] = StringLiteral(dt.isoformat())

    return True

def builtin_stamp_date_time(g, rt):

    rt._trace ('CALLED BUILTIN stamp_date_time', g)

    pred = g.terms[g.inx]

    args = pred.args
    if len(args) != 2:
        raise PrologRuntimeError('stamp_date_time: 2 args expected.', g.location)

    if not isinstance(args[1], Predicate) or not args[1].name == 'date' or len(args[1].args) != 7:
        raise PrologRuntimeError('stamp_date_time: arg1: date structure expected.', g.location)

    try:
        arg_Y   = rt.prolog_get_variable(args[1].args[0], g.env, g.location)
        arg_M   = rt.prolog_get_variable(args[1].args[1], g.env, g.location)
        arg_D   = rt.prolog_get_variable(args[1].args[2], g.env, g.location)
        arg_H   = rt.prolog_get_variable(args[1].args[3], g.env, g.location)
        arg_Mn  = rt.prolog_get_variable(args[1].args[4], g.env, g.location)
        arg_S   = rt.prolog_get_variable(args[1].args[5], g.env, g.location)
        arg_TZ  = rt.prolog_get_string(args[1].args[6], g.env, g.location)

        tz = get_localzone() if arg_TZ == 'local' else pytz.timezone(arg_TZ)

        arg_TS  = rt.prolog_get_string(args[0], g.env, g.location)

        #dt = datetime.datetime.fromtimestamp(arg_TS, tz)
        dt = dateutil.parser.parse(arg_TS).astimezone(tz)

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
        raise PrologRuntimeError('sub_string: 5 args expected.', g.location)

    arg_String    = rt.prolog_get_string(args[0], g.env, g.location)
    arg_Before    = rt.prolog_eval(args[1], g.env, g.location)
    arg_Length    = rt.prolog_eval(args[2], g.env, g.location) 
    arg_After     = rt.prolog_eval(args[3], g.env, g.location)  
    arg_SubString = rt.prolog_eval(args[4], g.env, g.location)  

    # FIXME: implement other variants
    if arg_Before:
        if not isinstance (arg_Before, NumberLiteral):
            raise PrologRuntimeError('sub_string: arg_Before: Number expected, %s found instead.' % arg_Before.__class__, g.location)
        before = int(arg_Before.f)
        
        if arg_Length:

            if not isinstance (arg_Length, NumberLiteral):
                raise PrologRuntimeError('sub_string: arg_Length: Number expected, %s found instead.' % arg_Length.__class__, g.location)
            length = int(arg_Length.f)

            if arg_After:
                raise PrologRuntimeError('sub_string: FIXME: arg_After required to be a variable for now.', g.location)
            else:

                var_After = rt.prolog_get_variable(args[3], g.env, g.location)
                if var_After != '_':
                    g.env[var_After] = NumberLiteral(len(arg_String) - before - length)

                if arg_SubString:
                    raise PrologRuntimeError('sub_string: FIXME: arg_SubString required to be a variable for now.', g.location)
                else:
                    var_SubString = rt.prolog_get_variable(args[4], g.env, g.location)

                    if var_SubString != '_':
                        g.env[var_SubString] = StringLiteral(arg_String[before:before + length])

        else:
            raise PrologRuntimeError('sub_string: FIXME: arg_Length required to be a literal for now.', g.location)
    else:
        raise PrologRuntimeError('sub_string: FIXME: arg_Before required to be a literal for now.', g.location)
        
    return True

def builtin_atom_chars(g, rt):

    rt._trace ('CALLED BUILTIN atom_chars', g)

    pred = g.terms[g.inx]
    args = pred.args
    if len(args) != 2:
        raise PrologRuntimeError('atom_chars: 2 args expected.', g.location)

    arg_atom   = rt.prolog_eval(args[0], g.env, g.location)
    arg_str    = rt.prolog_eval(args[1], g.env, g.location)

    if not arg_atom and not arg_str:
        raise PrologRuntimeError('atom_chars: exactly one arg has to be bound.', g.location)
    if arg_atom and arg_str:
        raise PrologRuntimeError('atom_chars: exactly one arg has to be bound.', g.location)

    if arg_atom:
        g.env[args[1].name] = StringLiteral(unicode(arg_atom))
    else:
        g.env[args[0].name] = Predicate(arg_str.s)
        
    return True

def builtin_write(g, rt):

    """ write (+Term) """

    rt._trace ('CALLED BUILTIN write', g)

    pred = g.terms[g.inx]
    args = pred.args
    if len(args) != 1:
        raise PrologRuntimeError('write: 1 arg (+Term) expected.', g.location)

    t = rt.prolog_eval(args[0], g.env, g.location)

    if isinstance (t, StringLiteral):
        sys.stdout.write(t.s)
    else:
        sys.stdout.write(unicode(t))
        
    return True
 
def builtin_nl(g, rt):

    rt._trace ('CALLED BUILTIN nl', g)

    pred = g.terms[g.inx]
    args = pred.args
    if len(args) != 0:
        raise PrologRuntimeError('nl: no args expected.', g.location)

    sys.stdout.write('\n')

    return True

def builtin_log(g, rt):

    """ log (+Level, +Term) """

    rt._trace ('CALLED BUILTIN log', g)

    pred = g.terms[g.inx]
    args = pred.args
    if len(args) != 2:
        raise PrologRuntimeError('log: 2 args (+Level, +Term) expected.', g.location)

    l = rt.prolog_get_constant(args[0], g.env, g.location)
    t = rt.prolog_eval        (args[1], g.env, g.location)

    if isinstance (t, StringLiteral):
        s = t.s
    else:
        s = unicode(t)
        
    if l == u'debug':
        logging.debug(s)
    elif l == u'info':
        logging.info(s)
    elif l == u'error':
        logging.error(s)
    else:
        raise PrologRuntimeError('log: unknown level %s, one of (debug, info, error) expected.' % l, g.location)

    return True
 
def builtin_trace(g, rt):

    """ trace (+OnOff) """

    rt._trace ('CALLED BUILTIN trace', g)

    pred = g.terms[g.inx]
    args = pred.args
    if len(args) != 1:
        raise PrologRuntimeError('trace: 1 arg (+OnOff) expected.', g.location)

    onoff = rt.prolog_get_constant(args[0], g.env, g.location)

    if onoff == u'on':
        rt.set_trace(True)
    elif onoff == u'off':
        rt.set_trace(False)
    else:
        raise PrologRuntimeError('trace: unknown onoff value %s, one of (on, off) expected.' % onoff, g.location)

    return True
 
def builtin_list_contains(g, rt):

    rt._trace ('CALLED BUILTIN list_contains', g)

    pred = g.terms[g.inx]

    args = pred.args
    if len(args) != 2:
        raise PrologRuntimeError('list_contains: 2 args expected.', g.location)

    arg_list   = rt.prolog_get_list (args[0], g.env, g.location)
    arg_needle = rt.prolog_eval(args[1], g.env, g.location)

    for o in arg_list.l:
        if o == arg_needle:
            return True

    return False

def builtin_list_nth(g, rt):

    rt._trace ('CALLED BUILTIN list_nth', g)

    pred = g.terms[g.inx]

    args = pred.args
    if len(args) != 3:
        raise PrologRuntimeError('list_nth: 3 args (index, list, elem) expected.', g.location)

    arg_idx  = rt.prolog_get_int  (args[0], g.env, g.location)
    arg_list = rt.prolog_get_list (args[1], g.env, g.location)
    arg_elem = rt.prolog_eval     (args[2], g.env, g.location)
    if not arg_elem:
        arg_elem = args[2]

    if not isinstance(arg_elem, Variable):
        raise PrologRuntimeError('list_nth: 3rd arg has to be an unbound variable for now, %s found instead.' % repr(arg_elem), g.location)

    g.env[arg_elem.name] = arg_list.l[arg_idx]

    return True

def builtin_list_slice(g, rt):

    """ list_slice (+Idx1, +Idx2, +List, -Slice) """

    rt._trace ('CALLED BUILTIN list_slice', g)

    pred = g.terms[g.inx]

    args = pred.args
    if len(args) != 4:
        raise PrologRuntimeError('list_slice: 4 args (+Idx1, +Idx2, +List, -Slice) expected.', g.location)

    arg_idx1  = rt.prolog_get_int  (args[0], g.env, g.location)
    arg_idx2  = rt.prolog_get_int  (args[1], g.env, g.location)
    arg_list  = rt.prolog_get_list (args[2], g.env, g.location)
    arg_slice = rt.prolog_eval     (args[3], g.env, g.location)
    if not arg_slice:
        arg_slice = args[3]

    if not isinstance(arg_slice, Variable):
        raise PrologRuntimeError('list_slice: 4th arg has to be an unbound variable for now, %s found instead.' % repr(arg_slice), g.location)

    g.env[arg_slice.name] = ListLiteral(arg_list.l[arg_idx1:arg_idx2])

    return True

def builtin_list_append(g, rt):

    """ list_append (?List, +Element) """

    rt._trace ('CALLED BUILTIN list_append', g)

    pred = g.terms[g.inx]

    args = pred.args
    if len(args) != 2:
        raise PrologRuntimeError('list_append: 2 args (?List, +Element) expected.', g.location)

    arg_list    = rt.prolog_get_variable (args[0], g.env, g.location)
    arg_element = rt.prolog_eval         (args[1], g.env, g.location)

    if not arg_list in g.env:
        g.env[arg_list] = ListLiteral([arg_element])
    else:
        l2 = deepcopy(g.env[arg_list].l)
        l2.append(arg_element)
        g.env[arg_list] = ListLiteral(l2)

    return True

def builtin_list_str_join(g, rt):

    """ list_str_join (+Glue, +List, -Str) """

    rt._trace ('CALLED BUILTIN list_str_join', g)

    pred = g.terms[g.inx]

    args = pred.args
    if len(args) != 3:
        raise PrologRuntimeError('list_str_join: 3 args (+Glue, +List, -Str) expected.', g.location)

    arg_glue  = rt.prolog_get_string (args[0], g.env, g.location)
    arg_list  = rt.prolog_get_list   (args[1], g.env, g.location)
    arg_str   = rt.prolog_eval       (args[2], g.env, g.location)
    if not arg_str:
        arg_str = args[2]

    if not isinstance(arg_str, Variable):
        raise PrologRuntimeError('list_str_join: 3rd arg has to be an unbound variable for now, %s found instead.' % repr(arg_slice), g.location)

    g.env[arg_str.name] = StringLiteral(arg_glue.join(map(lambda a: a.s if isinstance(a, StringLiteral) else unicode(a), arg_list.l)))

    return True

def builtin_dict_put(g, rt):

    """ dict_put (?Dict, +Key, +Value) """

    rt._trace ('CALLED BUILTIN dict_put', g)

    pred = g.terms[g.inx]

    args = pred.args
    if len(args) != 3:
        raise PrologRuntimeError('dict_put: 3 args (?Dict, +Key, +Value) expected.', g.location)

    arg_dict    = rt.prolog_get_variable (args[0], g.env, g.location)
    arg_key     = rt.prolog_get_constant (args[1], g.env, g.location)
    arg_val     = rt.prolog_eval         (args[2], g.env, g.location)

    if not arg_dict in g.env:
        g.env[arg_dict] = DictLiteral({arg_key: arg_val})
    else:
        d2 = deepcopy(g.env[arg_dict].d)
        d2[arg_key] = arg_val
        g.env[arg_dict] = DictLiteral(d2)

    return True

def builtin_dict_get(g, rt):

    """ dict_get (+Dict, ?Key, -Value) """

    rt._trace ('CALLED BUILTIN dict_get', g)

    pred = g.terms[g.inx]

    args = pred.args
    if len(args) != 3:
        raise PrologRuntimeError('dict_get: 3 args (+Dict, ?Key, -Value) expected.', g.location)

    arg_dict    = rt.prolog_get_dict     (args[0], g.env, g.location)
    arg_key     = rt.prolog_eval         (args[1], g.env, g.location)
    arg_val     = rt.prolog_get_variable (args[2], g.env, g.location)

    res = []

    if not arg_key:

        arg_key = rt.prolog_get_variable (args[1], g.env, g.location)

        for key in arg_dict.d:
            res.append({arg_key: StringLiteral(key), arg_val: arg_dict.d[key]})

    else:

        arg_key = rt.prolog_get_constant (args[1], g.env, g.location)
        res.append({arg_val: arg_dict.d[arg_key]})

    return res

ASSERT_OVERLAY_VAR_NAME = '__OVERLAYZ__'

def do_assertz(env, name, clause, res={}):

    ov = res.get(ASSERT_OVERLAY_VAR_NAME)
    if ov is None:
        ov = env.get(ASSERT_OVERLAY_VAR_NAME)

    if ov is None:
        res[ASSERT_OVERLAY_VAR_NAME] = {name: [clause]}
    else:
        d2 = deepcopy(ov)
        if name in d2:
            d2[name].append(clause)
        else:
            d2[name] = [clause]
        res[ASSERT_OVERLAY_VAR_NAME] = d2

    return res

def builtin_assertz(g, rt):

    """ assertz (+P) """

    rt._trace ('CALLED BUILTIN assertz', g)

    pred = g.terms[g.inx]

    args = pred.args
    if len(args) != 1:
        raise PrologRuntimeError('assertz: 1 arg (+P) expected.', g.location)

    arg_p  = rt.prolog_get_predicate (args[0], g.env, g.location)

    # if not arg_p:
    #     import pdb; pdb.set_trace()
    
    clause = Clause (head=arg_p, location=g.location)

    name = arg_p.name

    return [do_assertz(g.env, name, clause, res={})]

def do_assertz_predicate(env, name, args, res={}, location=None):

    """ convenience function: build Clause/Predicate structure, translate python string into Predicates/Variables by
        Prolog conventions (lowercase: predicate, uppercase: variable) """

    if not location:
        location = SourceLocation('<input>', 0, 0)

    mapped_args = []
    for arg in args:
        if not isinstance(arg, basestring):
            mapped_args.append(arg)
            continue
        if arg[0].isupper():
            mapped_args.append(Variable(arg))
        else:
            mapped_args.append(Predicate(arg))

    return do_assertz (env, name, Clause(head=Predicate(name, mapped_args), location=location), res=res)

def do_gensym(rt, root):

    orm_gn = rt.db.session.query(model.ORMGensymNum).filter(model.ORMGensymNum.root==root).first()

    if not orm_gn:
        current_num = 1
        orm_gn = model.ORMGensymNum(root=root, current_num=1)
        rt.db.session.add(orm_gn)
    else:
        current_num = orm_gn.current_num + 1
        orm_gn.current_num = current_num

    return root + str(current_num)

def builtin_gensym(g, rt):

    """ gensym (+Root, -Unique) """

    rt._trace ('CALLED BUILTIN gensym', g)

    pred = g.terms[g.inx]

    args = pred.args
    if len(args) != 2:
        raise PrologRuntimeError('gensym: 2 args (+Root, -Unique) expected.', g.location)

    arg_root   = rt.prolog_eval         (args[0], g.env, g.location)
    arg_unique = rt.prolog_get_variable (args[1], g.env, g.location)

    unique = do_gensym(rt, arg_root.name)

    g.env[arg_unique] = Predicate(unique)

    return True


#
# functions
#

def builtin_format_str(pred, env, rt, location):

    rt._trace_fn ('CALLED FUNCTION format_str', env)

    args  = pred.args
    arg_F = rt.prolog_get_string(args[0], env, location)

    if len(args)>1:
        
        a = map(lambda x: rt.prolog_get_literal(x, env, location), args[1:])

        f_str = arg_F % tuple(a)

    else:

        f_str = arg_F

    return StringLiteral(f_str)

def _builtin_list_lambda (pred, env, rt, l, location):

    args = pred.args
    if len(args) != 1:
        raise PrologRuntimeError('list builtin fn: 1 arg expected.')

    arg_list = rt.prolog_get_list (args[0], env, location)

    res = reduce(l, arg_list.l)
    return res, arg_list.l
    # if isinstance(res, (int, float)):
    #     return NumberLiteral(res)
    # else:
    #     return StringLiteral(unicode(res))

def builtin_list_max(pred, env, rt, location):

    rt._trace_fn ('CALLED FUNCTION list_max', env)

    return _builtin_list_lambda (pred, env, rt, lambda x, y: x if x > y else y, location)[0]

def builtin_list_min(pred, env, rt, location):

    rt._trace_fn ('CALLED FUNCTION list_min', env)

    return _builtin_list_lambda (pred, env, rt, lambda x, y: x if x < y else y, location)[0]

def builtin_list_sum(pred, env, rt, location):

    rt._trace_fn ('CALLED FUNCTION list_sum', env)

    return _builtin_list_lambda (pred, env, rt, lambda x, y: x + y, location)[0]

def builtin_list_avg(pred, env, rt, location):

    rt._trace_fn ('CALLED FUNCTION list_avg', env)

    l_sum, l = _builtin_list_lambda (pred, env, rt, lambda x, y: x + y, location)

    assert len(l)>0
    return l_sum / NumberLiteral(float(len(l)))

def builtin_list_len(pred, env, rt, location):

    rt._trace_fn ('CALLED FUNCTION list_len', env)

    args = pred.args
    if len(args) != 1:
        raise PrologRuntimeError('list builtin fn: 1 arg expected.')

    arg_list = rt.prolog_get_list (args[0], env, location)
    return NumberLiteral(len(arg_list.l))

