%prolog

woman(mia). 
woman(jody). 
woman(yolanda). 

man(joe).
man(fred).
man(bob).

human(X) :- woman(X);man(X).

