
=============
Syntreenet
=============

Free logics from PEGs
---------------------

Syntreenet facilitates easy development of any finite domain formal
theory possible in any language described by a `Parsing Expression Grammar`_.

It provides a knowledge base in the form of a performant and scalable
`production system`_, where rules and facts interact to produce new rules and
facts. Facts in this context are the top productions in the provided PEGs, and
rules are fundamentally composed of a set of those facts as conditions and
another set of facts as consecuences.

It's only dependence is on the excellent Parsimonious_ PEG parser by Erik Rose.

.. contents::

Example Usage
-------------

Let's start with a simple grammar with which we can build triples consisting on
a subject, a predicate, and an object, with 2 predicates, |element| and
|subset|, thus producing classifications of things. To make this example
simpler, we will use the ASCII string "element-of" in place of unicode |element|,
and "subset-of" in place of |subset|.

The grammar for this might be something like::

   fact        = word ws pred ws word
   pred        = element / subset
   element     = "element-of"
   subset      = "subset-of"
   word        = ~"[a-z0-9]+"
   ws          = ~"\s+"

With this, we can have facts such as::

  a element-of b
  b subset-of c
  c subset-of d

On top of this language, we might want a logic where, if the previous 3
facts are added to a knowledge base, it would also have that::

  a element-of c
  a element-of d
  b subset-of d

For this, we need a logic in which variables range over the "word" productions.
So we modify the grammar substituting the "word" rule with::

   word        = v_word / __var__
   v_word      = ~"[a-z0-9]+"

With this grammar we can now build a knowledge base, and add rules appropriate
for our purposes:

.. code:: python

   >>> from syntreenet import KnowledgeBase

   >>> grammar = """
   >>>    fact        = word ws pred ws word
   >>>    pred        = element / subset
   >>>    element     = "element-of"
   >>>    subset      = "subset-of"
   >>>    word        = v_word / __var__
   >>>    v_word      = ~"[a-z0-9]+"
   >>>    ws          = ~"\s+"
   >>> """

   >>> kb = KnowledgeBase(grammar)

   >>> kb.tell("X1 element-of X2 ; X2 subset-of X3 -> X1 element-of X3")
   >>> kb.tell("X1 subset-of X2 ; X2 subset-of X3 -> X1 subset-of X3")

Now we can add facts to the knowledge base, and query for them or for their
conscuences:

.. code:: python

   >>> kb.tell("a element-of b")
   >>> kb.tell("b subset-of c")
   >>> kb.tell("c subset-of d")

   >>> kb.query("a element-of b")
   True
   >>> kb.query("a element-of d")
   True
   >>> kb.query("c element-of d")
   False
   >>> kb.query("X1 subset-of d")
   [{'X1': 'b'}, {'X1': 'c'}]

Goals
-----

Scalability:
   Adding new facts or rules is essentially O(1) in the number of rules plus
   facts already present in the knowledge base. Theoretically, this is due to
   the fact that the DAGs that hold the data (facts and rules) are only ever
   searched by consulting Python_ dictionaries. Practically, I am getting a
   fairly constant value of a couple tenths of a millisecond per fact (this
   will depend on the complexity of the grammar), up to the capacity of my
   laptop (totalling around 2 million facts and rules). 

Universality:
   The "free" in the heading caption is in the sense of a `free object`_ over
   the formal languages described by PEGs: syntreenet knows nothing about the
   grammar underlying the particular logic it deals with at any particular
   moment.

Clear and tested code:
   The code follows best practices for readability and is tested with 99%
   coverage including branch analysis.

Detailed Usage
--------------

Install
.......

syntreenet_ is available at pypi_, just use pip in a Python >= 3.7
environment::

   $ pip install syntreenet
   $ python
   >>> import syntreenet

Test
....

To run the tests, you can download the sources from a mirror, create a Python_
environment for it, and use nose2_::

   $ git clone https://git.sr.ht/~enriquepablo/syntreenet
   $ cd syntreenet/
   $ virtualenv venv
   $ source venv/bin/activate
   $ python setup.py develop easy_install syntreenet[testing]
   $ nose2

Grammar requirements
....................

Note that these requirements can be overridden in the ``__init__`` method for
``KnowledgeBase``.

* The top production in the grammar must be called "fact".
* The productions that must be in the range of the logical variables must have
  a name starting with ``"v_"``.
* These "logical" productions must happen in higher productions as alternatives
  to the builtin production "__var__".
* To make rules, 2 sets of facts (the conditions and the consecuences) must be
  joined by semicolons, and joined among them with the string " -> ".
* Only conditions, consecuences, and queries can have variables in place of
  "logical" productions. Facts cannot.
* No grammar production can have a name starting and ending with 2 underscores.

* Variables start with an "X", followed by any number of digits.

Basic API
.........

The API is extremelly simple. As seen above, the entry point for syntreenet is
the ``KnowledgeBase`` class. It is instantiated with a string containing a PEG
appropriate for Parsimonious_ and subject to the restrictions stated above.

Objects of this class offer 3 methods:

* ``tell(self, sentence)``: accepts a fact or a rule in the form of a string and
  incorporates it to the knowledge base.
* ``query(self, fact)``: accepts a fact (possibly with variables) in the form of a string,
  and returns whether the fact can be found in the knowledge base. If it has
  variables, it will return the variable substitutions that result in facts
  present in the knowledge base, in the form of a dict of strings to strings.
* ``goal(self, fact)``: provided with a fact, it will return the facts that would be needed
  to get it to the knowledge base (without directly adding it). This is a form
  of backward chaining.



Copyright (c) 2019 by Enrique Pérez Arnaud <enrique@cazalla.net>

.. |element| unicode:: U+02208 .. element sign
.. |subset| unicode:: U+02286 .. subset sign

.. _syntreenet: http://www.syntree.net/
.. _GPLv3: https://www.gnu.org/licenses/gpl-3.0.txt
.. _pypi: https://pypi.org/project/syntreenet/
.. _`production system`: https://en.wikipedia.org/wiki/Production_system_%28computer_science%29
.. _`Parsing Expression Grammar`: https://en.wikipedia.org/wiki/Parsing_expression_grammar
.. _Python: http://www.python.org/
.. _syntreenet.scripts: https://git.sr.ht/~enriquepablo/syntreenet/tree/master/src/syntreenet/scripts/
.. _Parsimonious: https://github.com/erikrose/parsimonious
.. _nose2: https://docs.nose2.io/en/latest/
.. _`free object`: https://en.wikipedia.org/wiki/Free_object
