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

