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

from __future__ import annotations

import re
from copy import copy
from dataclasses import dataclass, field
from typing import List, Set, Union, cast

from .grammar import Segment, Path, Fact, Matching
from .factset import FactSet
from .ruleset import CondSet, ConsSet, Activation, Rule
from .logging import logger

from parsimonious.grammar import Grammar
from parsimonious.nodes import Node


EMPTY_MATCHING : Matching = Matching()
EMPTY_FACT : Fact = Fact('')

COMMON_RULES = '''
        __sentence__    = __rule__ / {fact}
        __rule__        = __conds__ __arrow__ __conss__
        __conds__       = ({fact} __ws__? __sc__? __ws__?)+
        __conss__       = ({fact} __ws__? __sc__? __ws__?)+
        __arrow__       = __ws__? "->" __ws__?
        __var__         = {var_pat}
        __ws__          = ~"\s*"
        __sc__          = {fact_sep}
'''

class KnowledgeBase:
    '''
    The object that contains both the graph of rules (or the tree of
    conditions) and the graph of facts.
    '''
    def __init__(self, grammar_text : str,
                 fact_rule : str = 'fact',
                 var_range_expr : str = '^v_',
                 var_pat : str = '~"_*X[0-9]+"',
                 fact_sep : str = '";"',
                 backend : str = 'parsimonious'):
        common = COMMON_RULES.format(fact=fact_rule,
                                     fact_sep=fact_sep, 
                                     var_pat=var_pat)
        self.grammar_text = f"{common}\n{grammar_text}"
        self.grammar = Grammar(self.grammar_text)
        self.fset = FactSet(kb=self)
        self.dset = CondSet(kb=self)
        self.sset = ConsSet(kb=self)
        self.activations : List[Activation] = list()
        self.processing = False
        self.counter = 0
        self.querying_rules = True
        self.seen_rules : Set[str] = set()
        self.fact_rule : str = fact_rule
        self.var_range_expr = re.compile(var_range_expr)

    def parse(self, s : str) -> Node:
        tree = self.grammar.parse(s)
        return tree.children[0]

    def in_var_range(self, path):
        return bool(self.var_range_expr.match(path[-1].expr.name))

    def tell(self, s : str):
        '''
        Add new sentence (rule or fact) to the knowledge base.
        '''
        tree = self.parse(s)
        if tree.expr.name == '__rule__':
            for child_node in tree.children:
                if child_node.expr.name == '__conds__':
                    cond_nodes = [ch.children[0] for ch in child_node.children]
                elif child_node.expr.name == '__conss__':
                    cons_nodes = [ch.children[0] for ch in child_node.children]
            conds = tuple(self.from_parse_tree(c) for c in cond_nodes)
            conss = tuple(self.from_parse_tree(c) for c in cons_nodes)
            rule = Rule(conds, conss)
            activation = Activation(rule, EMPTY_MATCHING, EMPTY_FACT, True)
        elif tree.expr.name == self.fact_rule:
            fact = self.from_parse_tree(tree)
            activation = Activation(fact, query_rules=False)
        self.activations.append(activation)
        self.process()

    def query(self, q : str) -> Union[List[Matching], bool]:
        tree = self.parse(q)
        qf = self.from_parse_tree(tree)
        response = self.ask(qf)
        if not response:
            return False
        if len(response) == 1 and not response[0].mapping:
            return True
        return response

    def ask(self, q : Fact) -> List[Matching]:
        '''
        Check whether a fact exists in the knowledge base, or, if it contains
        variables, find all the variable assigments that correspond to facts
        that exist in the knowledge base.
        '''
        return self.fset.ask_fact(q)

    def goal(self, q : str) -> list:
        tree = self.parse(q)
        qf = self.from_parse_tree(tree)
        return self.query_goal(qf)

    def query_goal(self, fact : Fact) -> list:
        self.sset.backtracks = []
        paths = fact.get_leaf_paths()
        matching = Matching(origin=fact)
        self.sset.propagate(paths, matching)
        fulfillments = []
        for bt in self.sset.backtracks:
            conds = [c.substitute(bt.matching, self) for c in
                    cast(Rule, bt.precedent).conditions]
            needed = []
            known = []
            for cond in conds:
                answers = self.ask(cond)
                if not answers:
                    needed.append(cond)
                else:
                    known.append(answers)

            for answs in known:
                for a in answs:
                    newf = list(n.substitute(a, self) for n in needed)
                    fulfillments.append(newf)
            if not known:
                fulfillments.append(needed)
        return fulfillments


    def _add_fact(self, fact : Fact):
        '''
        This method is the entry to the algorithm that checks for conditions
        that match a new fact being added to the knowledge base. 
        '''
        paths = fact.get_leaf_paths()
        matching = Matching(origin=fact)
        self.dset.propagate(paths, matching)

    def _new_rule_activation(self, act : Activation) -> Rule:
        rule = cast(Rule, act.precedent)
        conds = [c.substitute(act.matching, self) for c in
                rule.conditions if c != act.condition]
        new_conds = tuple(conds)
        cons = tuple(c.substitute(act.matching, self) for c in rule.consecuences)
        new_rule = Rule(new_conds, cons)
        self.dset.add_rule(new_rule)
        self.sset.add_rule(new_rule)
        return new_rule

    def _new_fact_activations(self, act : Activation):
        rule = cast(Rule, act.precedent)
        cons = tuple(c.substitute(act.matching, self) for c in rule.consecuences)
        acts = [Activation(c) for c in cons]
        self.activations.extend(acts)

    def _new_rule(self, act : Activation):
        rule = act.precedent
        for cond in cast(Rule, rule).conditions:
            answers = self.fset.ask_fact(cond)
            for a in answers:
                rulestr = str(rule) + str(a) + str(cond)
                if rulestr in self.seen_rules:
                    continue
                self.seen_rules.add(rulestr)
                act = Activation(rule, a, cond, True)
                self.activations.append(act)

    def process(self):
        '''
        Process all pending activations, and add the corresponding sentences to
        the knowledge base.
        '''
        if not self.processing:
            self.processing = True
            self.seen_rules = set()
            while self.activations:
                act = self.activations.pop(0)
                self.querying_rules = act.query_rules
                self.counter += 1
                s = act.precedent
                if isinstance(s, Fact):
                    if not self.ask(s):
                        logger.info(f'adding fact "{s}"')
                        self._add_fact(s)
                        self.fset.add_fact(s)
                elif isinstance(s, Rule):
                    if len(s.conditions) > 1 or act.condition is EMPTY_FACT:
                        new_rule = self._new_rule_activation(act)
                        logger.info(f'adding rule "{new_rule}"')
                        if self.querying_rules:
                            self._new_rule(act)
                    else:
                        self._new_fact_activations(act)

            self.processing = False

    def from_parse_tree(self, tree : Node) -> Fact:
        '''
        Build fact from a list of paths.
        '''
        segment_tuples : List[tuple] = []
        self._visit_pnode(tree, (), segment_tuples)
        paths = tuple(Path(s) for s in segment_tuples)
        return Fact(tree.text, paths)

    def _visit_pnode(self, node : Node, root_path : tuple,
            all_paths : List[tuple], parent : Node = None):
        expr = node.expr
        text = node.full_text[node.start: node.end]
        try:
            start = node.start - cast(Segment, parent).start
            end = node.end - cast(Segment, parent).start
        except AttributeError:  # node is root node
            start, end = 0, len(text)
        segment = Segment(text, expr, start, end, not bool(node.children))
        path = root_path + (segment,)
        if path[-1].leaf or self.in_var_range(path):
            all_paths.append(path)
        for child in node.children:
            self._visit_pnode(child, path, all_paths, parent=node)
