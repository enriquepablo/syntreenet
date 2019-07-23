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


import os
from unittest import TestCase
from syntreenet.kbase import KnowledgeBase
from parsimonious.grammar  import Grammar


HERE = os.path.abspath(os.path.dirname(__file__))


class GrammarTestCase(TestCase):

    grammar_file = ''
    var_range_expr = '^v_'

    def setUp(self):
        fn = os.path.join(HERE, '../../grammars', self.grammar_file)
        with open(fn, 'r') as fh:
            self.kb = KnowledgeBase(fh.read(),
                                    var_range_expr=self.var_range_expr)
            self.grammar = self.kb.grammar
