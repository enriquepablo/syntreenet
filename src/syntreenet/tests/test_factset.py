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

    def test_fact(self):
        tree = self.kb.parse('((ho ho))')
        f = self.kb.from_parse_tree(tree)
        self.kb.fset.add_fact(f)
        resp = self.kb.fset.ask_fact(f)
        self.assertTrue(resp)

    def test_other_fact(self):
        tree1 = self.kb.parse('((ho ho))')
        f1 = self.kb.from_parse_tree(tree1)
        tree2 = self.kb.parse('((hi hi))')
        f2 = self.kb.from_parse_tree(tree2)
        self.kb.fset.add_fact(f1)
        resp = self.kb.fset.ask_fact(f2)
        self.assertFalse(resp)

    def test_other_fact_italic(self):
        tree1 = self.kb.parse('((ho ho))')
        f1 = self.kb.from_parse_tree(tree1)
        tree2 = self.kb.parse("''ho ho''")
        f2 = self.kb.from_parse_tree(tree2)
        self.kb.fset.add_fact(f1)
        resp = self.kb.fset.ask_fact(f2)
        self.assertFalse(resp)

    def test_query_fact(self):
        tree1 = self.kb.parse('((ho ho))')
        f1 = self.kb.from_parse_tree(tree1)
        tree2 = self.kb.parse('((X1))')
        f2 = self.kb.from_parse_tree(tree2)

        self.kb.fset.add_fact(f1)
        resp = self.kb.fset.ask_fact(f2)

        val = f1.get_all_paths()[1].value
        var = f2.get_all_paths()[1].value

        self.assertEquals(resp[0][var], val)


class PairsTests(GrammarTestCase):
    grammar_file = 'pairs.peg'
    var_range_expr = '^(word|fact)$'

    def test_fact(self):
        tree = self.kb.parse('(hola : adios, hello : bye)')
        f = self.kb.from_parse_tree(tree)
        self.kb.fset.add_fact(f)
        resp = self.kb.fset.ask_fact(f)
        self.assertTrue(resp)

    def test_false_fact(self):
        tree1 = self.kb.parse('(hola : adios, hello : bye)')
        f1 = self.kb.from_parse_tree(tree1)
        tree2 = self.kb.parse('(hola : adios, bye : hello)')
        f2 = self.kb.from_parse_tree(tree2)
        self.kb.fset.add_fact(f1)
        resp = self.kb.fset.ask_fact(f2)
        self.assertFalse(resp)

    def test_nested_fact(self):
        tree = self.kb.parse('(es : (hola : adios), en : (hello : bye))')
        f = self.kb.from_parse_tree(tree)
        self.kb.fset.add_fact(f)
        resp = self.kb.fset.ask_fact(f)
        self.assertTrue(resp)

    def test_false_nested_fact(self):
        tree1 = self.kb.parse('(es : (hola : adios), en : (hello : bye))')
        f1 = self.kb.from_parse_tree(tree1)
        tree2 = self.kb.parse('(es : (hola : adios), en : (bye : hello))')
        f2 = self.kb.from_parse_tree(tree2)
        self.kb.fset.add_fact(f1)
        resp = self.kb.fset.ask_fact(f2)
        self.assertFalse(resp)

    def test_nested_fact_with_var(self):
        tree1 = self.kb.parse('(es : (hola : adios), en : (hello : bye))')
        f1 = self.kb.from_parse_tree(tree1)
        tree2 = self.kb.parse('(es : (hola : adios), en : (hello : X1))')
        f2 = self.kb.from_parse_tree(tree2)
        self.kb.fset.add_fact(f1)
        resp = self.kb.fset.ask_fact(f2)
        self.assertEquals(resp[0].mapping[0][0].text, 'X1')
        self.assertEquals(resp[0].mapping[0][1].text, 'bye')

    def test_nested_fact_with_2_vars(self):
        tree1 = self.kb.parse('(es : (hola : adios), en : (hello : bye))')
        f1 = self.kb.from_parse_tree(tree1)
        tree2 = self.kb.parse('(es : (hola : X1), en : (hello : X2))')
        f2 = self.kb.from_parse_tree(tree2)
        self.kb.fset.add_fact(f1)
        resp = self.kb.fset.ask_fact(f2)
        self.assertEquals(resp[0].mapping[0][0].text, 'X1')
        self.assertEquals(resp[0].mapping[0][1].text, 'adios')
        self.assertEquals(resp[0].mapping[1][0].text, 'X2')
        self.assertEquals(resp[0].mapping[1][1].text, 'bye')

    def test_nested_fact_with_nonterminal_var(self):
        tree1 = self.kb.parse('(es : (hola : adios), en : (hello : bye))')
        f1 = self.kb.from_parse_tree(tree1)
        tree2 = self.kb.parse('(es : (hola : adios), en : X1)')
        f2 = self.kb.from_parse_tree(tree2)
        self.kb.fset.add_fact(f1)
        resp = self.kb.fset.ask_fact(f2)
        self.assertEquals(resp[0].mapping[0][0].text, 'X1')
        self.assertEquals(resp[0].mapping[0][1].text, '(hello : bye)')

    def test_nested_fact_with_2_nonterminal_vars(self):
        tree1 = self.kb.parse('(es : (hola : adios), en : (hello : bye))')
        f1 = self.kb.from_parse_tree(tree1)
        tree2 = self.kb.parse('(es : X1, en : X2)')
        f2 = self.kb.from_parse_tree(tree2)
        self.kb.fset.add_fact(f1)
        resp = self.kb.fset.ask_fact(f2)
        self.assertEquals(resp[0].mapping[0][0].text, 'X1')
        self.assertEquals(resp[0].mapping[0][1].text, '(hola : adios)')
        self.assertEquals(resp[0].mapping[1][0].text, 'X2')
        self.assertEquals(resp[0].mapping[1][1].text, '(hello : bye)')

    def test_nested_facts_with_2_nonterminal_vars(self):
        tree1 = self.kb.parse('(es : (hola : adios), en : (hello : bye))')
        f1 = self.kb.from_parse_tree(tree1)
        tree2 = self.kb.parse('(es : (hola : adios), en : (hullo : gbye))')
        f2 = self.kb.from_parse_tree(tree2)
        self.kb.fset.add_fact(f1)
        self.kb.fset.add_fact(f2)
        tree3 = self.kb.parse('(es : X1, en : X2)')
        f3 = self.kb.from_parse_tree(tree3)
        resp = self.kb.fset.ask_fact(f3)
        self.assertEquals(resp[0].mapping[0][0].text, 'X1')
        self.assertEquals(resp[0].mapping[0][1].text, '(hola : adios)')
        self.assertEquals(resp[0].mapping[1][0].text, 'X2')
        self.assertEquals(resp[0].mapping[1][1].text, '(hello : bye)')

        self.assertEquals(resp[1].mapping[1][0].text, 'X2')
        self.assertEquals(resp[1].mapping[1][1].text, '(hullo : gbye)')

    def test_nested_fact_with_repeated_var(self):
        tree1 = self.kb.parse('(es : (hola : adios), en : (hello : adios))')
        f1 = self.kb.from_parse_tree(tree1)
        tree2 = self.kb.parse('(es : (hola : X1), en : (hello : X1))')
        f2 = self.kb.from_parse_tree(tree2)
        self.kb.fset.add_fact(f1)
        resp = self.kb.fset.ask_fact(f2)
        self.assertEquals(resp[0].mapping[0][0].text, 'X1')
        self.assertEquals(resp[0].mapping[0][1].text, 'adios')

    def test_nested_fact_substitute(self):
        tree1 = self.kb.parse('(es : (hola : adios), en : (hello : bye))')
        f1 = self.kb.from_parse_tree(tree1)
        tree2 = self.kb.parse('(es : X1, en : X2)')
        f2 = self.kb.from_parse_tree(tree2)
        pair = f1.get_all_paths()[4][-1]
        self.assertEquals(str(pair), '(hola : adios)')
        var = f2.get_leaf_paths()[3][-1]
        self.assertEquals(str(var), 'X1')
        matching = g.Matching(((pair, var),))
        self.assertEquals(repr(matching), '<Match: (hola : adios) : X1>')
        new = f1.substitute(matching, self.kb)
        self.assertEquals(repr(new), '<Fact <(es : X1, en : (hello : bye))>')
        with self.assertRaises(KeyError):
            matching[g.Segment('foo')]

        new_matching = matching.setitem(pair, pair)
        self.assertEquals(repr(new_matching), '<Match: (hola : adios) : (hola : adios)>')
        with self.assertRaises(ValueError):
            matching.merge(new_matching)


class ClassesTests(GrammarTestCase):
    grammar_file = 'classes.peg'

    def test_repeated(self):
        self.kb.tell("X1 is X2 ; X2 is X3 -> X1 is X3")
        self.kb.tell("X1 isa X2 ; X2 is X3 -> X1 isa X3")
        self.kb.tell('animal is thing')
        self.kb.tell('mammal is animal')
        self.kb.tell('primate is mammal')
        self.kb.tell('human is primate')
        self.kb.tell('vegetable is thing')
        self.kb.tell('tree is vegetable')
        self.kb.tell('pine is tree')
        sets = ('thing', 'animal', 'mammal', 'primate', 'human',
                'vegetable', 'tree', 'pine')
        l = len(sets)
        for i in range(200):
            s = sets[i % l]
            fact = f'{s}{i} isa {s}'
            self.kb.tell(fact)
        self.assertEquals(self.kb.counter, 2385)

    def test_one_hundred(self):
        from ..ruleset import RuleSet
        with self.assertRaises(NotImplementedError):
            RuleSet().get_cons(rule=None)
        with self.assertRaises(NotImplementedError):
            RuleSet().add_activation(act=None)
