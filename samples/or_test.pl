%prolog

woman(mia). 
woman(jody). 
woman(yolanda). 

man(joe).
man(fred).
man(bob).

child(alice).
child(jeanne).
child(rascal).

not_dog(alice).
not_dog(jeanne).

human(X) :- woman(X);man(X);child(X),not_dog(X).

