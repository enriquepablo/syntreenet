# Copyright (c) 2019 by Enrique Pérez Arnaud <enrique@cazalla.net>
#
# This file is part of the syntreenet project.
# https://syntree.net
#
# The syntreenet project is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# The syntreenet project is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with any part of the terms project.
# If not, see <http://www.gnu.org/licenses/>.

import syntreenet.grammar as g
from . import GrammarTestCase


class BoldTextTests(GrammarTestCase):
    grammar_file = 'bold-text.peg'

    def test_simple_rule(self):
        self.kb.tell("((X1)) -> ''uu''")
        self.kb.tell('((ho ho))')
        resp = self.kb.query("''uu''")
        self.assertTrue(resp)

    def test_simple_rule_after(self):
        self.kb.tell('((ho ho))')
        self.kb.tell("((X1)) -> ''uu''")
        resp = self.kb.query("''uu''")
        self.assertTrue(resp)

    def test_simple_rule_2(self):
        self.kb.tell("((X1)) -> ''X1''")
        self.kb.tell('((ho ho))')
        resp = self.kb.query("''ho ho''")
        self.assertTrue(resp)

    def test_simple_rule_2_after(self):
        self.kb.tell('((ho ho))')
        self.kb.tell("((X1)) -> ''X1''")
        resp = self.kb.query("''ho ho''")
        self.assertTrue(resp)

    def test_simple_rule_3(self):
        self.kb.tell("((X1)) ''X2'' -> ''X1'' ((X2))")
        self.kb.tell('((ho ho))')
        self.kb.tell("''hi hi''")
        resp = self.kb.query("((hi hi))")
        self.assertTrue(resp)

    def test_simple_rule_3_after(self):
        self.kb.tell('((ho ho))')
        self.kb.tell("''hi hi''")
        self.kb.tell("((X1)) ''X2'' -> ''X1'' ((X2))")
        resp = self.kb.query("((hi hi))")
        self.assertTrue(resp)

    def test_simple_rule_3_extra_cond(self):
        self.kb.tell('((ho ho))')
        self.kb.tell("''hi hi''")
        self.kb.tell("((X1)) {{logic}''X2''} -> ''X1'' ((X2))")
        resp = self.kb.query("((hi hi))")
        self.assertTrue(resp)

    def test_remove(self):
        self.kb.tell('((ho ho))')
        self.kb.tell("''hi hi''")
        resp = self.kb.query("((ho ho))")
        self.assertTrue(resp)
        self.kb.tell('rm ((ho ho))')
        resp = self.kb.query("((ho ho))")
        self.assertFalse(resp)
        resp = self.kb.query("''hi hi''")
        self.assertTrue(resp)

    def test_non_remove(self):
        self.kb.tell('((ho ho))')
        resp = self.kb.query("((ho ho))")
        self.assertTrue(resp)
        self.kb.tell('rm ((he he))')
        resp = self.kb.query("((ho ho))")
        self.assertTrue(resp)

    def test_simple_rule_raise(self):
        self.kb.tell("((X1)) {{python}raise Exception()} -> ''uu''")
        self.kb.tell('((ho ho))')
        resp = self.kb.query("''uu''")
        self.assertFalse(resp)

    def test_simple_rule_test_false(self):
        self.kb.tell("((X1)) {{python}test = False} -> ''uu''")
        self.kb.tell('((ho ho))')
        resp = self.kb.query("''uu''")
        self.assertFalse(resp)


class ClassesTests(GrammarTestCase):
    grammar_file = 'classes.peg'

    def test_simple_rule(self):
        self.kb.tell("X1 is X2 ; X2 is X3 -> X1 is X3")
        self.kb.tell("X1 isa X2 ; X2 is X3 -> X1 isa X3")
        self.kb.tell('animal is thing')
        self.kb.tell('human is animal')
        self.kb.tell('susan isa human')
        resp = self.kb.query("human is thing")
        self.assertTrue(resp)
        resp = self.kb.query("susan isa thing")
        self.assertTrue(resp)
        resp = self.kb.query("human isa thing")
        self.assertFalse(resp)
        resp = self.kb.goal("human isa thing")
        self.assertEquals(len(resp), 4)

    def test_simple_rule_after(self):
        self.kb.tell('animal is thing')
        self.kb.tell('human is animal')
        self.kb.tell('susan isa human')
        self.kb.tell("X1 is X2 ; X2 is X3 -> X1 is X3")
        self.kb.tell("X1 isa X2 ; X2 is X3 -> X1 isa X3")
        resp = self.kb.query("human is thing")
        self.assertTrue(resp)
        resp = self.kb.query("susan isa thing")
        self.assertTrue(resp)
        resp = self.kb.query("human isa thing")
        self.assertFalse(resp)
        resp = self.kb.goal("human isa thing")
        self.assertEquals(len(resp), 4)


class PairsTests(GrammarTestCase):
    grammar_file = 'pairs.peg'
    var_range_expr = '^(word|fact)$'

    def test_simple_rule(self):
        self.kb.tell('''(es : (salutation : X1) , en : (salutation : X2)) ; \
                        (person : (name : X3)) \
                        -> \
                        (greeting : (es : (greeting : X1 , to : X3) , \
                                     en : (greeting : X2 , to : X3))) \
        ''')
        self.kb.tell('(es : (salutation : hola) , en : (salutation : hello))')
        self.kb.tell('(person : (name : susan))')
        resp = self.kb.query("(greeting : (es : (greeting : hola , to : susan) , \
                                     en : (greeting : hello , to : susan)))")
        self.assertTrue(resp)

    def test_simple_rule_after_the_facts(self):
        self.kb.tell('(es : (salutation : hola) , en : (salutation : hello))')
        self.kb.tell('(person : (name : susan))')
        self.kb.tell('''(es : (salutation : X1) , en : (salutation : X2)) ; \
                        (person : (name : X3)) \
                        -> \
                        (greeting : (es : (greeting : X1 , to : X3) , \
                                     en : (greeting : X2 , to : X3))) \
        ''')
        resp = self.kb.query("(greeting : (es : (greeting : hola , to : susan) , \
                                     en : (greeting : hello , to : susan)))")
        self.assertTrue(resp)

    def test_simple_rule_2(self):
        self.kb.tell('''(wants : she , what : X1) \
                        -> \
                        (gets : she , what : X1) \
        ''')
        self.kb.tell('(wants : she , what : (thing : every , when : always))')
        resp = self.kb.query("(gets : she , what : (thing : every , when : always))")
        self.assertTrue(resp)

    def test_simple_rule_with_similar_conds(self):
        self.kb.tell('''(wants : X1 , what : X2 , for : X1) \
                        -> \
                        (gets : X1 , what : X2) \
        ''')
        self.kb.tell('''(wants : X1 , what : X2 , for : X1 , in : here) \
                        -> \
                        (puts : X1 , what : X2) \
        ''')
        self.kb.tell('(wants : she , what : (thing : every , when : always), for : she)')
        self.kb.tell('(wants : she , what : (thing : every , when : always), for : she , in : here)')
        resp = self.kb.query("(gets : she , what : (thing : every , when : always))")
        self.assertTrue(resp)
        resp = self.kb.query("(puts : she , what : (thing : every , when : always))")
        self.assertTrue(resp)

    def test_simple_rule_with_similar_conds_after(self):
        self.kb.tell('(wants : she , what : (thing : every , when : always), for : she)')
        self.kb.tell('(wants : she , what : (thing : every , when : always), for : she , in : here)')
        self.kb.tell('''(wants : X1 , what : X2 , for : X1) \
                        -> \
                        (gets : X1 , what : X2) \
        ''')
        self.kb.tell('''(wants : X1 , what : X2 , for : X1 , in : here) \
                        -> \
                        (puts : X1 , what : X2) \
        ''')
        resp = self.kb.query("(gets : she , what : (thing : every , when : always))")
        self.assertTrue(resp)
        resp = self.kb.query("(puts : she , what : (thing : every , when : always))")
        self.assertTrue(resp)


class ScoreTests(GrammarTestCase):
    grammar_file = 'score.peg'

    def test_simple_rule(self):
        self.kb.tell('''score X1 X2 ;
                        {{logic}max-score X3 X4} ;
                        {{python}X2 > X4}
                        ->
                        rm max-score X3 X4 ;
                        max-score X1 X2''')
        self.kb.tell('max-score nobody 0')
        self.kb.tell('score susan 19')
        self.kb.tell('score john 9')
        resp = self.kb.query('max-score susan 19')
        self.assertTrue(resp)
        self.kb.tell('score paul 1')
        self.kb.tell('score lil 29')
        resp = self.kb.query('max-score lil 29')
        self.assertTrue(resp)

    def test_simple_rule_2(self):
        self.kb.tell('''score X1 X2 ;
                        {{logic}mean X3 X4 X5} ;
                        {{python}X6 = X3 + 1; X7 = X4 + X2; X8 = X7 / X6}
                        ->
                        rm mean X3 X4 X5 ;
                        mean X6 X7 X8''')
        self.kb.tell('mean 0 0 0')
        self.kb.tell('score susan 19')
        self.kb.tell('score john 9')
        self.kb.tell('score paul 1')
        self.kb.tell('score lil 29')
        resp = self.kb.query('mean X1 X2 X3')
        self.assertTrue(resp)

    def test_simple_rule_3(self):
        self.kb.tell('''score X1 X2 ;
                        max-score nobody X9 ; 
                        {{logic}mean X3 X4 X5} ;
                        {{python}X6 = X3 + 1; X7 = X4 + X2; X8 = X7 / X6}
                        ->
                        rm mean X3 X4 X5 ;
                        mean X6 X7 X8''')
        self.kb.tell('mean 0 0 0')
        self.kb.tell('max-score nobody 0')
        self.kb.tell('score susan 19')
        self.kb.tell('score john 9')
        self.kb.tell('score paul 1')
        self.kb.tell('score lil 29')
        resp = self.kb.query('mean X1 X2 X3')
        self.assertTrue(resp)

    def test_simple_rule_both(self):
        self.kb.tell('''score X1 X2 ;
                        {{logic}mean X3 X4 X5} ;
                        {{python}X6 = X3 + 1; X7 = X4 + X2; X8 = X7 / X6}
                        ->
                        rm mean X3 X4 X5 ;
                        mean X6 X7 X8''')
        self.kb.tell('''score X1 X2 ;
                        {{logic}max-score X3 X4} ;
                        {{python}X2 > X4}
                        ->
                        rm max-score X3 X4 ;
                        max-score X1 X2''')
        self.kb.tell('max-score nobody 0')
        self.kb.tell('mean 0 0 0')
        self.kb.tell('score susan 19')
        self.kb.tell('score john 9')
        self.kb.tell('score paul 1')
        self.kb.tell('score lil 29')
        resp = self.kb.query('max-score lil 29')
        self.assertTrue(resp)
        resp = self.kb.query('mean 4.0 58.0 14.5')
        self.assertTrue(resp)



'''
person is thing
document is thing
context is thing
placed isa verb
action isa verb
permission is thing
role is thing
has-role isa verb
has-permission isa verb
want isa verb
status is thing
has-status isa verb


person want action document
person has-role in context
role has-permission
document has-status
document placed in context
permission protects action for status
->
action document
'''
