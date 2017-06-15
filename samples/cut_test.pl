
foo(R, X) :- X is 1, R is 'one',!.
foo(R, X) :- X is 2, R is 'two',!.
foo(R, X) :- R is 'many'.

numbers(1).
numbers(2).
numbers(3).
numbers(4).

bar(R,X) :- numbers(X), foo(R,X).

