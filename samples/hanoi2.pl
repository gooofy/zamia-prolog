%prolog


% move(N,X,Y,Z) - move N disks from peg X to peg Y, with peg Z being the
%                 auxilliary peg
%
% Strategy:
% Base Case: One disc - To transfer a stack consisting of 1 disc from 
%    peg X to peg Y, simply move that disc from X to Y 
% Recursive Case: To transfer n discs from X to Y, do the following: 
%    Transfer the first n-1 discs to some other peg X 
%    Move the last disc on X to Y 
%    Transfer the n-1 discs from X to peg Y

%
% this version calls a custom python builtin record_move to demonstrate embedding HAL-Prolog
%

move(1,X,Y,_) :-  
    write('Move top disk from '), 
    write(X), 
    write(' to '), 
    write(Y), 
    record_move(X,Y),
    nl. 
move(N,X,Y,Z) :- 
    N>1, 
    M is N-1, 
    move(M,X,Z,Y), 
    move(1,X,Y,_), 
    move(M,Z,Y,X).  

