% prolog

chancellor_endtimes (angela_merkel, [1, 2, []]).
chancellor_endtimes (helmut_kohl, [1,2,3]).

is_chancellor(PERSON) :-
    chancellor_endtimes(PERSON, ENDTIMES),
    list_contains(ENDTIMES, []).

was_chancellor(PERSON) :-
    chancellor_endtimes(PERSON, ENDTIMES),
    not (is_chancellor(PERSON)).

chancellor (angela_merkel).
chancellor (helmut_kohl).

