
a universal production rule system with below logarithmic time complexity with
respect to both productions and activations.

 * production rule system: In this system we keep sentences and we keep rules.
   We call knowledge base to the set of rules and sentences that the sytem
   keeps at any given time. The syntax of the sentences, as we shall see
   below, is pluggable. Rules are made up of 2 sets of sentences, the
   conditions and the consecuences, that can contain universally quantified
   logic variables. When a new sentence is added to the system, it will check
   with it the conditions of the rules, and if any matches, a new activation is
   produced, that results in either a new rule or in new sentences.
 
 * Universal: The syntax of the sentences the system deals with is puggable.
   Any syntax whose sentences can be represented as trees can be plugged in.

 * logarithmic time complexity: Whenever we add a sentence to the system and it
   matches the condition of some rule, there will be an activation. An
   activation will always result in either a new rule or in new sentences. So
   in this system rules are cheap, and in a typical situation there may be more
   rules than sentences. For these reasons, the appropriate parameter of
   complexity here is the activation - though we will analyse complexity in
   terms of other variables. And, in terms of activations (i.e., in terms of
   the size of the knowledge base), the time complexity for new activations,
   both theoretical and experimental, is below logarithmic.


Using.

I will provide here an example of using the software, to give a practical view
of what is this about. As said, the syntax is pluggable; for the example here I
will use a very simple syntax, defined in babel.ont, which allows us to
produce classifications of things: finite domain first order set theories. So
for example we will be able to have a knowledge base where we say that we have
a set of things, a subset of living things, a subset of animals, a subset of
mammals, etc.; and, if we tell the system that "my dog toby" belongs to the set
of animals, and we ask it whether "my dog toby" belongs to the set of things
(which is a superset of animals), it should answer yes.

In this system, we have sentences that are triples of words, and words that can
be of 2 kinds: predicates and atoms. We have 2 predicates, "belongs to" and
"subset of", and any number of atoms. Each sentence is composed of an atom as
subject, a predicate as verb, and a second atom as object. For example, we may
have as sentences:

  animal subset of thing
  primate subset of animal
  human subset of primate
  john belongs to human

To impose a finite domain set theory on this syntax, we would add rules:

  X1 belongs to X2;
  X2 subset of X3
  ->
  X1 belongs to X3.

  X1 subset of X2;
  X2 subset of X3
  ->
  X1 subset of X3.

With these rules and the previous sentences, we would also have that "human
subset of thing" and that "john belongs to animal", etc.

So, this is how we'd do it with syntreenet, using the syntax file provided in
babel.ont ( and shortening "belongs to" to "isa", and "subset of" to "is":

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

The output for this with logging set to INFO would be:

    adding rule "X1 isa X2; X2 is X3 -> X1 isa X3"
    adding rule "X1 is X2; X2 is X3 -> X1 is X3"
    adding sentence "animal is thing"
    adding rule "X1 isa animal -> X1 isa thing"
    adding rule "thing is X3 -> animal is X3"
    adding rule "X1 is animal -> X1 is thing"
    adding sentence "mammal is animal"
    adding rule "X1 isa mammal -> X1 isa animal"
    adding rule "animal is X3 -> mammal is X3"
    adding rule "X1 is mammal -> X1 is animal"
    adding sentence "mammal is thing"
    adding rule "X1 isa mammal -> X1 isa thing"
    adding rule "thing is X3 -> mammal is X3"
    adding rule "X1 is mammal -> X1 is thing"
    adding sentence "primate is mammal"
    adding rule "X1 isa primate -> X1 isa mammal"
    adding rule "mammal is X3 -> primate is X3"
    adding rule "X1 is primate -> X1 is mammal"
    adding sentence "primate is animal"
    adding sentence "primate is thing"
    adding rule "X1 isa primate -> X1 isa animal"
    adding rule "animal is X3 -> primate is X3"
    adding rule "X1 is primate -> X1 is animal"
    adding rule "X1 isa primate -> X1 isa thing"
    adding rule "thing is X3 -> primate is X3"
    adding rule "X1 is primate -> X1 is thing"
    adding sentence "human is primate"
    adding rule "X1 isa human -> X1 isa primate"
    adding rule "primate is X3 -> human is X3"
    adding rule "X1 is human -> X1 is primate"
    adding sentence "human is mammal"
    adding sentence "human is animal"
    adding sentence "human is thing"
    adding rule "X1 isa human -> X1 isa mammal"
    adding rule "mammal is X3 -> human is X3"
    adding rule "X1 is human -> X1 is mammal"
    adding rule "X1 isa human -> X1 isa animal"
    adding rule "animal is X3 -> human is X3"
    adding rule "X1 is human -> X1 is animal"
    adding rule "X1 isa human -> X1 isa thing"
    adding rule "thing is X3 -> human is X3"
    adding rule "X1 is human -> X1 is thing"
    adding sentence "susan isa human"
    adding rule "human is X3 -> susan isa X3"
    adding sentence "susan isa primate"
    adding sentence "susan isa mammal"
    adding sentence "susan isa animal"
    adding sentence "susan isa thing"
    adding rule "primate is X3 -> susan isa X3"
    adding rule "mammal is X3 -> susan isa X3"
    adding rule "animal is X3 -> susan isa X3"
    adding rule "thing is X3 -> susan isa X3"


Algorithmic analysis:
There are 2 tree structures involved: one in which each leaf represents a
condition in some rule(s), the rules tree, and one in which each leaf
represents a fact, the facts tree. The rules tree is searched every time a new
rule or a new sentence is added to the knowledge base, and the facts tree is
searched whenever a new sentence is added or whenever a query is made.

All the steps in any of the searches -all choices of a branch in an (n-ary)
fork- are made by consulting hash tables. This means that, theoretically, the
time complexity of these operations (adding rules and sentences, or querying
the sentences) is below logarithmic with respect to the number of leafs - it
would be logarithmic if all leafs where provided in a single hash table.

As regards the spatial complexity, it is quite bad, but in this respect this is
just a proof of concept: we are dealing here with many Python lists and
dictionaries, and I have not been careful in keeping just one copy of each
immutable object. 2 million sentences + rules were taking about 1.2 GB in my
laptop.

There is a precise algorithmic (time) analysis in the comments to the code,
marked as comments starting with "AA", and with a different code and step
numbering for the different operations so that they can be grepped and ordered.

Experimentally, running the benchmarking script in scripts.benchmark_ont, which
takes the animal ontology sketched above and adds any number of sentences with
the form "animal234 isa animal", "mammal21 is a mammal", etc, with 100, 1000,
10000 and 100000 sentences, the results were:

    $ python -m src.scripts.benchmark_ont -n 100
    took 0.15968937100842595 s to proccess 2157 activations
        mean for activation : 0.07403308808920998ms

    $ python -m src.scripts.benchmark_ont -n 1000
    took 1.6106685880076839 s to proccess 20737 activations
        mean for activation : 0.07767124405688788ms

    $ python -m src.scripts.benchmark_ont -n 10000
    took 16.57817696798884 s to proccess 212133 activations
        mean for activation : 0.07814991994639608ms
    
    $ python -m src.scripts.benchmark_ont -n 100000
    took 163.85796326400305 s to proccess 2097412 activations
        mean for activation : 0.0781238799358462ms

So with 100000 sentences (corresponding to more than 2 million activations),
for this simple syntax, we were already reaching the asimptote.
