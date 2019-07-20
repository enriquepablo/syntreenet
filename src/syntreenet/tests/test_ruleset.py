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
        self.kb.tell("{{((X1)) -> ''uu''}}")
        self.kb.tell('((ho ho))')
        resp = self.kb.query("''uu''")
        self.assertTrue(resp)

    def test_simple_rule_2(self):
        self.kb.tell("{{((X1)) -> ''X1''}}")
        self.kb.tell('((ho ho))')
        resp = self.kb.query("''ho ho''")
        self.assertTrue(resp)

    def test_simple_rule_3(self):
        self.kb.tell("{{((X1)) ''X2'' -> ''X1'' ((X2))}}")
        self.kb.tell('((ho ho))')
        self.kb.tell("''hi hi''")
        resp = self.kb.query("((hi hi))")
        self.assertTrue(resp)


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
        resp = self.kb.goal("human isa thing")
        self.assertFalse(resp)
