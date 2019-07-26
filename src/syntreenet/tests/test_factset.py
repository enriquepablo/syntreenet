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


'''
(person : X1 , score : X2) ; (max-score X3 , by : X4) ; <<python> {X2} > {X3} >
-> rm (max-score X3 , by : X4) ; (max-score : X2 , by : X1)
'''
