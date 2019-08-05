
=============
Syntreenet
=============

-----------------------
Free logics from PEGs
-----------------------

Syntreenet facilitates easy development of any finite domain formal
theory possible in any language described by a Parsing Expression Grammar.

It provides a knowledge base in the form of a performant and scalable
production system, where rules and facts interact to produce new rules and
facts. Facts in this context are the top productions in the provided PEGs, and
rules are fundamentally composed of a set of those facts as conditions and
another set of facts as consecuences.

It uses the excellent Parsimonious_ PEG parser by Erik Rose.

Example Usage
-------------

Let's start with a simple grammar with which we can build triples consisting on
a subject, a predicate, and an object, with 2 predicates, |element| and
|subset|, thus producing classifications of things. To make this example
simpler, we will use the ASCII string "element-of" in place of the unicode point |element|,
and "subset-of" in place of |subset|.

The grammar for this might be something like::

   fact        = word ws pred ws word
   pred        = element / subset
   element     = "element-of"
   subset      = "subset-of"
   word        = ~"[a-z0-9]+"
   ws          = ~"\s+"

With this, we can have "facts" such as::

  a element-of b
  b subset-of c
  c subset-of d

On top of this language, we might want a logic where, if you add the previous 3
facts to a knowledge base, you would also have that::

  a element-of c
  a element-of d
  b subset-of d

For this, we need a logic in which variables range over the "word" productions.
So we modify the grammar substituting the "word" rule with::

   word        = v_word / __var__
   v_word      = ~"[a-z0-9]+"

With this grammar we can now build a knowledge base, and add rules appropriate
for our purposes::

   grammar = """
      fact        = word ws pred ws word
      pred        = element / subset
      element     = "element-of"
      subset      = "subset-of"
      word        = v_word / __var__
      v_word      = ~"[a-z0-9]+"
      ws          = ~"\s+"
   """

   kb = KnowledgeBase(grammar)

   kb.tell("X1 element-of X2 ; X2 subset-of X3 -> X1 element-of X3")
   kb.tell("X1 subset-of X2 ; X2 subset-of X3 -> X1 subset-of X3")

   kb.tell("a element-of b")
   kb.tell("b subset-of c")
   kb.tell("c subset-of d")



.. |element| unicode:: U+02208 .. element sign
.. |subset| unicode:: U+02286 .. subset sign
