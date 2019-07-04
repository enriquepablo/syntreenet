
A library to develop production rule systems with match cost logarithmic in the
size of the knowledge base (rules + facts).


Basic concepts and terminology.

Here I talk about rule production systems, with the kind of functionality
offered by e.g. CLIPS or Jess, i.e., the kind provided by the RETE algorithm
and derivatives (among which this present work might be placed).

The terminology I will use here is probably not the most common, but I hope it
is not uncommon enough to be original. I will speak of rules where others speak
of productions; rules that can have any number of conditions and consecuences
(consecuances rather than actions, to stress the fact that the only actions
implemented so far are assertions,) and which can contain logical variables,
scoped to the rules in which they appear. I will call facts to what some people
call WMEs (working memory elements). 

With 2trees, the grammar for the facts (and thus for the conditions and
consecuences) can (has to) be plugged in. The tools to define grammars
offered by the library are custom, so that they do not adhere to any
standard or convention, and are fairly free. Basically any grammar whose
productions (facts) can be represented as trees can be plugged in (but see
the next paragraph for a clarification). This grammar must be provided in
the form of productions of facts from syntagms - which are defined in
whatever ad-hoc manner. The only basic requirements for syntagms is that
they can tell whether they represent a logical variable or not, and that
they have a unique string representation.

Since a fact can always be represented as a tree, it means that it can also be
represented as a set of tuples, each tuple being the path from the root to a
leaf in the tree; and we can use these tuples to identify each syntactic
component of the fact, and use the set to reconstruct the fact. So if the
sentences that the grammar produces can be provided with 2 functions that are
inverse, one that takes any fact and results in a set of tuples of syntagms,
and one that takes a set of tuples of syntagms and returns the corresponding
fact (or warns about the set not corresponding to any well formed fact), this
grammar can be plugged in to 2trees. This allows us to abstract away the
library from grammatical concerns. "Whatever your grammar is, provide me your
productions as sets of hashable tuples of syntagms; now I can use those to make
hashtables of nodes". Or, for short, "give me your paths, and I'll use them in
my hash tables".

A final conceptual element is that facts and rules are, both in the way they
are represented in the network, and in the sense of their typical numbers, very
similar, and so we use the term sentence to refer to both facts and rules. A
knowedge base is, then, a set of sentences, to which we can add new sentences,
or query for facts.

Installation and usage.

Use pip. The package has no dependencies outside Python's standard library. It
is a very small package (~750loc according to SLOCCount) moderately documented
in the sources, just import from it.

A preliminary example usage.

I will continue here with an example of using the software, to give a practical
view of what is this about. If it is not immediately clear, just read on from
the following section.

As said, the grammar is pluggable; for the example here I will use a very simple
grammar, defined in babel.ont, which allows us to produce classifications of
things: finite domain first order set theories with set inclusion forming a
DAG. So for example we will be able to have a knowledge base where we say that
we have a set of things, a set of animals subset of things, etc.; and, if we
tell the system that "my dog toby" belongs to the set of animals, and we ask it
whether "my dog toby" belongs to the set of things, it should answer yes.

With this grammar, we have facts that are triples of words, and words that
can be of 2 kinds: predicates and atoms. We have 2 predicates, "belongs to" and
"subset of", and any number of atoms. Each fact is composed of an atom as
subject, a predicate as verb, and a second atom as object. For example, we may
have as facts:

  animal subset of thing.
  primate subset of animal.
  human subset of primate.
  susan belongs to human.

To impose a finite domain set theory on this grammar, we can add rules:

  X1 belongs to X2;
  X2 subset of X3
  ->
  X1 belongs to X3.

  X1 subset of X2;
  X2 subset of X3
  ->
  X1 subset of X3.

(I don't mean to be enforcing a DAG with these rules, I'm just offering a
simple example).

With these rules and the previous facts, we would also have that "human
subset of thing" and that "susan belongs to animal", etc.

So, this is how we'd do it with 2trees, using the grammar file provided in
babel.ont (and shortening "belongs to" to "isa", and "subset of" to "is"):

    from syntreenet.ruleset import Rule, KnowledgeBase
    from syntreenet.babel.ont import Word, Sen, isa, is_

    kb = KnowledgeBase()

    X1 = Word('X1', var=True)
    X2 = Word('X2', var=True)
    X3 = Word('X3', var=True)


    prem1 = Sen(X1, isa, X2)
    prem2 = Sen(X2, is_, X3)
    cons1 = Sen(X1, isa, X3)

    rule1 = Rule((prem1, prem2), (cons1,))

    prem3 = Sen(X1, is_, X2)
    cons2 = Sen(X1, is_, X3)

    rule2 = Rule((prem3, prem2), (cons2,))

    kb.tell(rule1)
    kb.tell(rule2)


    thing = Word('thing')
    animal = Word('animal')
    mammal = Word('mammal')
    primate = Word('primate')
    human = Word('human')
    susan = Word('susan')

    kb.tell(Sen(animal, is_, thing))
    kb.tell(Sen(mammal, is_, animal))
    kb.tell(Sen(primate, is_, mammal))
    kb.tell(Sen(human, is_, primate))

    kb.tell(Sen(susan, isa, human))

The logs produced by running the above code are:

    adding rule "X1 isa X2; X2 is X3 -> X1 isa X3"
    adding rule "X1 is X2; X2 is X3 -> X1 is X3"
    adding fact "animal is thing"
    adding rule "X1 isa animal -> X1 isa thing"
    adding rule "thing is X3 -> animal is X3"
    adding rule "X1 is animal -> X1 is thing"
    adding fact "mammal is animal"
    adding rule "X1 isa mammal -> X1 isa animal"
    adding rule "animal is X3 -> mammal is X3"
    adding rule "X1 is mammal -> X1 is animal"
    adding fact "mammal is thing"
    adding rule "X1 isa mammal -> X1 isa thing"
    adding rule "thing is X3 -> mammal is X3"
    adding rule "X1 is mammal -> X1 is thing"
    adding fact "primate is mammal"
    adding rule "X1 isa primate -> X1 isa mammal"
    adding rule "mammal is X3 -> primate is X3"
    adding rule "X1 is primate -> X1 is mammal"
    adding fact "primate is animal"
    adding fact "primate is thing"
    adding rule "X1 isa primate -> X1 isa animal"
    adding rule "animal is X3 -> primate is X3"
    adding rule "X1 is primate -> X1 is animal"
    adding rule "X1 isa primate -> X1 isa thing"
    adding rule "thing is X3 -> primate is X3"
    adding rule "X1 is primate -> X1 is thing"
    adding fact "human is primate"
    adding rule "X1 isa human -> X1 isa primate"
    adding rule "primate is X3 -> human is X3"
    adding rule "X1 is human -> X1 is primate"
    adding fact "human is mammal"
    adding fact "human is animal"
    adding fact "human is thing"
    adding rule "X1 isa human -> X1 isa mammal"
    adding rule "mammal is X3 -> human is X3"
    adding rule "X1 is human -> X1 is mammal"
    adding rule "X1 isa human -> X1 isa animal"
    adding rule "animal is X3 -> human is X3"
    adding rule "X1 is human -> X1 is animal"
    adding rule "X1 isa human -> X1 isa thing"
    adding rule "thing is X3 -> human is X3"
    adding rule "X1 is human -> X1 is thing"
    adding fact "susan isa human"
    adding rule "human is X3 -> susan isa X3"
    adding fact "susan isa primate"
    adding fact "susan isa mammal"
    adding fact "susan isa animal"
    adding fact "susan isa thing"
    adding rule "primate is X3 -> susan isa X3"
    adding rule "mammal is X3 -> susan isa X3"
    adding rule "animal is X3 -> susan isa X3"
    adding rule "thing is X3 -> susan isa X3"


Algorithmic analysis:

In his Thesis, "Production Matching for Large Learning Systems" (1995),
Robert B. Doorenbos says that:

   Our analysis asks under what circumstances efficient matching can be
   guaranteed. By "efficient" we mean the match cost should be (1) polynomial
   in W, the number of WMEs in working memory; (2) polynomial in C,
   the number of conditions per production; and (3) sublinear in
   P, the number of productions.

Here I claim to have a match cost logarithmic in W, logarithmic in C, and
logarithmic in P, so it is a stretch. I will try to justify this claim, first,
in the following few paragraphs, with an abstract explanation of the
structures and algorithms involved, and second, in the code, with a detailed
line by (relevant) line analysis of the different code paths. Since the full
library is just around 650 loc (as measured by SLOCCount), this detailed
analysis is not hard to follow. This claim is also tentatively supported by
some experimental evidence, which I'll provide further below.

There are 2 tree structures involved in this algorithm: one in which each leaf
represents a condition in some rule(s) (the rules tree), and one in which each
leaf represents a fact (the facts tree). In both trees each node has exactly
one parent and any number of children, arranged in a hash table.

The rules tree is searched every time a new rule or a new fact is added to
the knowledge base, and the facts tree is searched whenever a new fact is
added or whenever a query is made. All the steps in all of the searches -all
choices of a branch in an (n-ary) fork- are made by consulting hash tables.
This means that, theoretically, the time complexity of these operations (adding
rules and facts, or querying the facts) is at worst logarithmic with
respect to the number of leafs - it would be logarithmic if all leafs were
provided in a single hash table.

So the trick is to turn the tests that lead the descent through the branches to
the leaves into consultations to hash tables; and at the same time keep some
internal structure to the hashable objects so that we can play with logical
variables within said tests.

As regards the spatial complexity, it can be better, and in this respect this
is just a proof of concept: we are dealing here with many fat Python lists
(which allow random access but we only access sequentially) and dictionaries.
5 million facts + rules were taking about 3 GB in my laptop, and took
about 160s to process.

The specific procedures involved are the following.

Adding a rule.  We process each condition sequentially.  Each condition will
correspond to a leaf in the tree, that may or may not already exist. So the
rule tree is searched for the condition. If not found, from the node that is
furthest from the root and corresponds to (part of) the condition, we add the
missing nodes to reach the desired leaf. In the leaf we will reference the
needed information to produce activations when the condition is matched by a
fact, basically the rule it belogs to (so each leaf will have a set of rules,
all of which have the corresponding condition).

Adding a fact to the fact tree.
This follows the same steps as adding a condition to the rule tree. However,
whereas conditions can contain variables, facts cannot, and since variables
are reflected in the structure of the tree, the facts tree is simpler, and
adding a new fact also so.

Querying the fact tree.
We query the facts tree with facts that can contain variables, similar to
conditions in rules.
If there are no variables, there is just one possible leaf as target, and we
descend through the tree choosing each child node from a hash table.
If there are variables, they will match all the children of the corresponding
parent node, so the cost of a query will be linear wrt the number of answers it
will find.

Adding a fact to the system.
When we add a fact to the system, it is first queried from the fact set. If
there is a match, the operation is aborted.
Then it is checked with the rule set. For each of the conditions that match, an
activation is produced and stored to be processed later.
Finally, it is added to the fact set.

Adding a sentence to the system.
When a rule is added to the system, it is simply added to the rule tree.
When a fact is added, it is made into an activation, and processing of
activations starts; and processing of the fact can result in new activations,
which will be processed sequentially (this provides a linear dependence on
the amount of consecuences that any given fact will have, which has a very weak
dependence on the size of the kb, and a dominant one on the shape of the logic
being processed.)

Processing an activation produced by a fact matching a condition.
If a fact matches a condition, there will be an assignment of variables in the
condition to syntagms in the fact.
If the condition is the only one the rule has, the consecuences will be added
as activations, with any variable replaced with the assignment; all variables
must be taken care of by the assignment, i.e., any variable in the consecuences
must happen in the conditions.
If the rule has more conditions, we create a new rule, substituting the
variables in the assignment in all remaining conditions and consecuences (in
this case there may be remaining variables - not all conditions must contain
all variables), and add it to the rule tree.

Experimental results.

I have run a few very limited experiments with the benchmarking scripts in the
scripts submodule, which test both CLIPS and duarboj with the animal ontology
sketched above and adds a number of facts with the form "animal234 isa
animal", "mammal21 isa mammal", etc. A few notes about these experiments:

 * I have not extracted any statistics for lack of data points; these results
   are not meant as evidence, but as suggestive.

 * We are pitching a very optimized and tested C program against a proof of
   concept in 750 lines of Python. And it shows, the basal performance of CLIPS
   is an order of magnitude higher.

 * We are also hitting here a sweet spot for CLIPS, with just 2 rules and just
   2 conditions in each. Due to the different architecture duarboj does not
   share this sweet spot (it should perform the same with many more rules,
   since in fact in all the tests it ends up with 1000...s of rules).

 * To perform more extensive and conclusive tests I would need more hardware -
   and more time. Also ideally a proper implementation of the algorithm (again,
   time) in a more appropriate language - I am considering either Haskell or
   Rust for a canonical implementation, I guess that Haskell would be more
   fun, but Rust more performant.

I have run the benchmarks adding 1_000, 5_000, 10_000, 50_000, 100_000, 500_000,
and 1_000_000 facts, and I have calculated the mean of 6 runs for each point,
which is what is plotted. Very clearly the results are not conclusive, however,
a trend can be seen, where there is an steady increase in the cost of adding a
new fact for CLIPS, and a steadying out of the cost for duarboj.

<<PICS>>

Providing grammars

The elements to build grammars are basically 2 classes that have to be
extended, Fact and Syntagm. Each syntagm must have a unique string
representation, must be hashable, and must be capable of saying whether it is a
variable or not. Syntagms can have any internal structure as wanted, and can be
combined in any way to form facts. 

The main requirement for extensions of Syntagm is that they provide __str__,
__hash__, and a boolean method is_var().

Extensions of Fact must implement a get_paths() method that returns a
representation of the fact as a set of tuples of syntagms, and a classmethod
from_paths() inverse of the previous:

    x.__class__.from_paths(x.get_paths()) == x
