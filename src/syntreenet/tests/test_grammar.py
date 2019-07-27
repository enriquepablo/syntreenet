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

    def test_get_paths(self):
        tree = self.kb.parse('((ho ho))')
        f = self.kb.from_parse_tree(tree)
        all_paths = f.get_all_paths()
        leaf_paths = f.get_leaf_paths()
        self.assertEquals(len(all_paths), 3)
        self.assertEquals(len(leaf_paths), 3)

    def test_paths(self):
        tree1 = self.kb.parse('((ho ho))')
        f1 = self.kb.from_parse_tree(tree1)
        tree2 = self.kb.parse('((X1))')
        f2 = self.kb.from_parse_tree(tree2)

        self.assertEquals(f1.get_all_paths()[0][0].text, '((ho ho))')
        self.assertEquals(repr(f1.get_all_paths()[0][0]),
                '<Segment: fact: ((ho ho))>')
        self.assertEquals(repr(f1.get_all_paths()[0]),
                '<Path: fact - bold_text - bold_open - ((>')
        self.assertEquals(f1.get_all_paths()[0][0].name, 'fact')
        self.assertEquals(f1.get_all_paths()[0].value.text, '((')
        self.assertEquals(f1.get_all_paths()[0].value.name, 'bold_open')
        self.assertEquals(f1.get_all_paths()[0].is_leaf(), True)
        self.assertEquals(self.kb.in_var_range(f1.get_all_paths()[0]), False)
        self.assertEquals(f1.get_all_paths()[0].is_var(), False)

        self.assertEquals(f1.get_all_paths()[1][0].text, '((ho ho))')
        self.assertEquals(f1.get_all_paths()[1][0].name, 'fact')
        self.assertEquals(f1.get_all_paths()[1].value.text, 'ho ho')
        self.assertEquals(f1.get_all_paths()[1].value.name, 'v_text')
        self.assertEquals(f1.get_all_paths()[1].is_leaf(), True)
        self.assertEquals(self.kb.in_var_range(f1.get_all_paths()[1]), True)
        self.assertEquals(f1.get_all_paths()[1].is_var(), False)

        self.assertEquals(f1.get_all_paths()[2][0].text, '((ho ho))')
        self.assertEquals(f1.get_all_paths()[2][0].name, 'fact')
        self.assertEquals(f1.get_all_paths()[2].value.text, '))')
        self.assertEquals(f1.get_all_paths()[2].value.name, 'bold_close')
        self.assertEquals(f1.get_all_paths()[2].is_leaf(), True)
        self.assertEquals(self.kb.in_var_range(f1.get_all_paths()[2]), False)
        self.assertEquals(f1.get_all_paths()[2].is_var(), False)

        self.assertEquals(f2.get_all_paths()[1].value.text, 'X1')
        self.assertEquals(f2.get_all_paths()[1].is_var(), True)

        self.assertEquals(f1.get_all_paths()[0], f2.get_all_paths()[0])
        self.assertNotEqual(f1.get_all_paths()[1], f2.get_all_paths()[1])
        self.assertEquals(f1.get_all_paths()[2], f2.get_all_paths()[2])

    def test_substitute_path(self):
        tree1 = self.kb.parse('((ho ho))')
        f1 = self.kb.from_parse_tree(tree1)
        tree2 = self.kb.parse('((X1))')
        f2 = self.kb.from_parse_tree(tree2)

        val_path = f1.get_all_paths()[1]
        self.assertEquals(val_path.is_var(), False)

        var_path = f2.get_all_paths()[1]
        self.assertEquals(var_path.is_var(), True)

        matching = g.Matching(((var_path.value, val_path.value),))

        new_path, old_path = var_path.substitute(matching)

        self.assertEquals(old_path, var_path)
        self.assertEquals(old_path.deep_identity_tuple, var_path.deep_identity_tuple)
        self.assertEquals(new_path, val_path)
        self.assertEquals(new_path.deep_identity_tuple, val_path.deep_identity_tuple)

    def test_substitute(self):
        tree1 = self.kb.parse('((hi hi))')
        f1 = self.kb.from_parse_tree(tree1)
        tree2 = self.kb.parse('((X1))')
        f2 = self.kb.from_parse_tree(tree2)

        val = f1.get_all_paths()[1].value
        self.assertEquals(val.text, 'hi hi')

        var = f2.get_all_paths()[1].value
        self.assertEquals(var.text, 'X1')

        matching = g.Matching(((var, val),))

        f3 = f2.substitute(matching, self.kb)

        self.assertTrue(f3 == f1)

        orig_dit = f1.get_all_paths()[1].deep_identity_tuple
        subs_dit = f3.get_all_paths()[1].deep_identity_tuple

        self.assertTrue(orig_dit == subs_dit)

    def test_normalize(self):
        tree = self.kb.parse('((X1))')
        f = self.kb.from_parse_tree(tree)

        paths = f.normalize(self.kb)

        self.assertTrue(f.get_all_paths()[1].value.text, '__X1')
