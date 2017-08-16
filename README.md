# Zamia Prolog

Scalable and embeddable compiler/interpreter for a Zamia-Prolog (a Prolog dialect). Stores its knowledge base in a
Database via SQLAlchemy - hence the scalability, i.e. the knowledge base is not limited by the amount of RAM available.

Zamia-Prolog is written in pure python so it can be easily embedded into other python applications. Compiler and runtime
have interfaces to register custom builtins which can either be evaluated at compile time (called directives in
Zamia-Prolog) or at runtime.

The Prolog core is based on http://openbookproject.net/py4fun/prolog/prolog3.html by Chris Meyers.

While performance is definitely important, right now Chris' interpreted approach is more than good enough for my needs. 

My main focus here is embedding and language features - at the time of this writing I am experimenting with
incorporating some imperative concepts into Zamia-Prolog, such as re-assignable variables and if/then/else constructs.  
So please note that this is a Prolog dialect that probably never will be compliant to any Prolog standards. Instead it will
most likely drift further away from standard prolog and may evolve into my own logic-based language.

Features
========

* pure Python implementation
* easy to embed in Python applications
* easy to extend with custom builtins for domain specific tasks
* re-assignable variables with full backtracking support
* assertz/retract with full backtracking support (using database overlays)
* imperative language constructs such as if/then/else
* pseudo-variables/-predicates that make DB assertz/retractz easier to code

Requirements
============

*Note*: probably incomplete.

* Python 2.7
* py-nltools
* SQLAlchemy

Usage
=====

Compile `hanoi1.pl` example:

```python
from zamiaprolog.logicdb import LogicDB
from zamiaprolog.parser  import PrologParser

db_url = 'sqlite:///foo.db'
db     = LogicDB(db_url)
parser = PrologParser()

parser.compile_file('samples/hanoi1.pl', 'unittests', db)
```

now run a sample goal:

```python
from zamiaprolog.runtime import PrologRuntime

clause = parser.parse_line_clause_body('move(3,left,right,center)')
rt     = PrologRuntime(db)

solutions = rt.search(clause)
```

output:

```
Move top disk from left to right
Move top disk from left to center
Move top disk from right to center
Move top disk from left to right
Move top disk from center to left
Move top disk from center to right
Move top disk from left to right
```

Accessing Prolog Variables from Python
--------------------------------------

Set var X from python:
```python
clause = parser.parse_line_clause_body('Y is X*X')
solutions = rt.search(clause, {'X': NumberLiteral(3)})
```

check number of solutions:
```python
print len(solutions)
```
output:
```
1
```

access prolog result Y from python:
```python
print solutions[0]['Y'].f
```
output:
```
9
```

Custom Python Builtin Predicates
--------------------------------

To demonstrate how to register custom predicates with the interpreter, we will
introduce a python builtin to record the moves in our Hanoi example:

```python
recorded_moves = []

def record_move(g, rt):
    global recorded_moves

    pred = g.terms[g.inx]
    args = pred.args

    arg_from  = rt.prolog_eval(args[0], g.env)
    arg_to    = rt.prolog_eval(args[1], g.env) 

    recorded_moves.append((arg_from, arg_to))

    return True

rt.register_builtin('record_move', record_move)


```

now, compile and run the `hanoi2.pl` example:

```python
parser.compile_file('samples/hanoi2.pl', 'unittests', db)
clause = parser.parse_line_clause_body('move(3,left,right,center)')
solutions = rt.search(clause)
```
output:
```
Move top disk from left to right
Move top disk from left to center
Move top disk from right to center
Move top disk from left to right
Move top disk from center to left
Move top disk from center to right
Move top disk from left to right
```
now, check the recorded moves:
```python
print len(recorded_moves)
print repr(recorded_moves)
```
output:
```
7
[(Predicate(left), Predicate(right)), (Predicate(left), Predicate(center)), (Predicate(right), Predicate(center)), (Predicate(left), Predicate(right)), (Predicate(center), Predicate(left)), (Predicate(center), Predicate(right)), (Predicate(left), Predicate(right))]
```

Generate Multiple Bindings from Custom Predicates
-------------------------------------------------

Custom predicates not only can return True/False and manipulate the environment directly to generate a single binding as
in

```python
def custom_pred1(g, rt):

    rt._trace ('CALLED BUILTIN custom_pred1', g)

    pred = g.terms[g.inx]
    args = pred.args
    if len(args) != 1:
        raise PrologRuntimeError('custom_pred1: 1 arg expected.')

    arg_var  = rt.prolog_get_variable(args[0], g.env)
       
    g.env[arg_var] = NumberLiteral(42)

    return True
```

they can also return a list of bindings which will then result in one prolog result each. In this example,
we generate 4 bindings of two variables each:

```python
def multi_binder(g, rt):

    global recorded_moves

    rt._trace ('CALLED BUILTIN multi_binder', g)

    pred = g.terms[g.inx]
    args = pred.args
    if len(args) != 2:
        raise PrologRuntimeError('multi_binder: 2 args expected.')

    var_x  = rt.prolog_get_variable(args[0], g.env)
    var_y  = rt.prolog_get_variable(args[1], g.env) 

    res = []
    for x in range(2):

        lx = NumberLiteral(x)

        for y in range(2):
            ly = NumberLiteral(y)

            res.append({var_x: lx, var_y: ly})

    return res
```
so running
```python
clause = self.parser.parse_line_clause_body('multi_binder(X,Y)')
solutions = self.rt.search(clause)
```
will produce 4 solutions:
```
[{u'Y': 0, u'X': 0}, {u'Y': 1, u'X': 0}, {u'Y': 0, u'X': 1}, {u'Y': 1, u'X': 1}]
```

Custom Compiler Directives
--------------------------

Besides custom builtins we can also have custom compiler-directives in Zamia-Prolog. Directives are evalutated at compile
time and will not be stored in the database. 

Here is an example: First, register your custom directive:

```python 
def _custom_directive (module_name, clause, user_data):
    print "_custom_directive has been called. clause: %s user_data:%s" % (clause, user_data)

parser.register_directive('custom_directive', _custom_directive, None)
```

now, compile a piece of prolog code that uses the directive:

```python
parser.parse_line_clauses('custom_directive(abc, 42, \'foo\').')

```
output:
```
_custom_directive has been called. clause: custom_directive(abc, 42.0, "foo"). user_data:None
[]
```

Re-Assignable Variables 
-----------------------

Variables can be re-assigned using the built-in special `set` (`:=`):

```prolog
Z := 23, Z := 42
```
this comes with full backtracking support.

Pseudo-Variables/-Predicates
----------------------------

This is an extension to standard prolog syntax found in Zamia-Prolog to make "variable" setting and access
easier:
```
C:user        -> user (C, X)
C:user:name   -> user (C, X), name (X, Y)
self:name     -> name (self, X)
self:label|de -> label (self, de, X)
```
this works for evaluation as well as setting/asserting (left-hand and right-hand side of expressions).

Example:
```prolog
assertz(foo(bar, 23)), bar:foo := 42, Z := bar:foo
```
will result in `Z == 42` and `foo(bar, 42)` asserted in the database.

if/then/else/endif
------------------

```prolog
if foo(bar) then
   do1, do2
else
   do2, do3
endif

```
is equivalent to
```prolog
or ( and (foo(bar), do1, do2), and (not(foo(bar)), do2, do3) )
```

License
=======

My own scripts as well as the data I create is LGPLv3 licensed unless otherwise noted in the script's copyright headers.

Some scripts and files are based on works of others, in those cases it is my
intention to keep the original license intact. Please make sure to check the
copyright headers inside for more information.

Author
======

* Guenter Bartsch <guenter@zamia.org>
* Chris Meyers.
* Heiko Schäfer <heiko@schaefer.name>

