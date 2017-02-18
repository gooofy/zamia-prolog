# HAL Prolog

Scalable and embeddable compiler/interpreter for a HAL-Prolog (a Prolog dialect). Stores its knowlegde base in a
Database via SQLAlchemy - hence the scalability, i.e. the knowlegde base is not limited by the amount of RAM available.

HAL Prolog is written in pure python so it can be easily embedded into other python applications. Compiler and runtime
have interfaces to register custom builtins which can either be evaluated at compile time (called directives in
HAL-Prolog) or at runtime.

The Prolog core is based on http://openbookproject.net/py4fun/prolog/prolog3.html by Chris Meyers.

I do have vague plans to turn this into a proper WAM based Prolog implementation at some point, but right now Chris'
interpreted approach is more than good enough for my needs. Also please note that this is a Prolog dialect that probably
never will be compliant to any Prolog standards. The goal here is to have a Prolog-style reasoning engine that can be
embedded in applications, customized for domain-specific tasks - not to implement a pure, standards-compliant,
standalone Prolog System meant for application development.

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
from halprolog.logicdb import LogicDB
from halprolog.parser  import PrologParser

db_url = 'sqlite:///foo.db'
db     = LogicDB(db_url)
parser = PrologParser()

parser.compile_file('samples/hanoi1.pl', 'unittests', db)
```

now run a sample goal:

```python
from halprolog.runtime import PrologRuntime

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

