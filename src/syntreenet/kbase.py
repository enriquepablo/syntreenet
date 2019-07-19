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

from copy import copy
from dataclasses import dataclass, field
from typing import List, Dict, Union, Tuple, Any, Optional, Union, cast

from .grammar import Segment, Path, Fact, Matching
from .factset import FactSet
from .ruleset import CondSet, ConsSet, Activation, Rule
from .logging import logger

from parsimonious.grammar import Grammar


EMPTY_MATCHING : Matching = Matching()
EMPTY_FACT : Fact = Fact('')

class KnowledgeBase:
    '''
    The object that contains both the graph of rules (or the tree of
    conditions) and the graph of facts.
    '''
    def __init__(self, grammar_text : str, backend : str = 'parsimonious'):
        self.grammar = Grammar(grammar_text)
        self.fset = FactSet(kb=self)
        self.dset = CondSet(kb=self)
        self.sset = ConsSet(kb=self)
        self.activations : List[Activation] = list()
        self.processing = False
        self.counter = 0
        self.querying_rules = True

    def tell(self, s : str):
        '''
        Add new sentence (rule or fact) to the knowledge base.
        '''
        tree = self.grammar.parse(s)
        if tree.expr.name == 'rule':
            for child_node in tree.children:
                if child_node.expr.name == 'conds':
                    cond_nodes = child_node.children
                elif child_node.expr.name == 'conss':
                    cons_nodes = child_node.children
            conds = tuple(Fact.from_parse_tree(c) for c in cond_nodes)
            conss = tuple(Fact.from_parse_tree(c) for c in cons_nodes)
            rule = Rule(conds, conss)
            activation = Activation(rule, EMPTY_MATCHING, EMPTY_FACT, True)
        elif tree.expr.name == 'fact':
            fact = Fact.from_parse_tree(tree)
            activation = Activation(fact, query_rules=False)
        self.activations.append(activation)
        self.process()

    def ask(self, q : Fact) -> Union[List[Matching], bool]:
        '''
        Check whether a fact exists in the knowledge base, or, if it contains
        variables, find all the variable assigments that correspond to facts
        that exist in the knowledge base.
        '''
        response = self.fset.ask_fact(q)
        if not response:
            return False
        if len(response) == 1 and not response[0].mapping:
            return True
        return response

    def query_goal(self, fact : Fact) -> list:
        self.sset.backtracks = []
        paths = fact.get_all_paths()
        matching = Matching(origin=fact)
        self.sset.propagate(list(paths), matching)
        fulfillments = []
        for bt in self.sset.backtracks:
            conds = [c.substitute(bt.matching, self) for c in
                    cast(Rule, bt.precedent).conditions]
            needed = []
            known = []
            for cs in conds:
                for cond in cs:
                    answers = self.ask(cond)
                    if answers is False:
                        needed.append(cond)
                    elif not answers is True:
                        known.append(answers)
            if known:
                preresults = []
                results = known[0]
                for more in known[1:]:
                    for p in cast(List[Matching], results):
                        for a in cast(List[Matching], more):
                            try:
                                preresults.append(p.merge(a))
                            except ValueError:
                                pass
                    results = preresults
                    preresults = []
                needed = [[n.substitute(m, self) for n in cast(List[Fact], needed)]
                        for m in cast(List[Matching], results)]

            fulfillments.append(needed)
        return fulfillments


    def _add_fact(self, fact : Fact):
        '''
        This method is the entry to the algorithm that checks for conditions
        that match a new fact being added to the knowledge base. 
        '''
        logger.debug(f'adding fact "{fact}" to rete')
        paths = fact.get_leaf_paths()
        matching = Matching(origin=fact)
        self.dset.propagate(list(paths), matching)

    def _new_rule_activation(self, act : Activation):
        rule = cast(Rule, act.precedent)
        conds = [c.substitute(act.matching, self) for c in
                rule.conditions if c != act.condition]
        new_conds = tuple(tuple(cs) for cs in conds)
        cons = tuple(c.substitute(act.matching, self) for c in rule.consecuences)
        new_rule = Rule(new_conds, cons)
        self.dset.add_rule(new_rule)
        self.sset.add_rule(new_rule)
        for cond in conds:
            answers = self.ask(cond)
            for a in cast(List[Matching], answers):
                act = Activation(new_rule, a, cond, True)
                self.activations.append(act)

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
                act = Activation(rule, a, cond, True)
                self.activations.append(act)

    def process(self):
        '''
        Process all pending activations, and add the corresponding sentences to
        the knowledge base.
        '''
        if not self.processing:
            self.processing = True
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
                    if len(s.conditions) > 1:
                        self._new_rule_activation(act)
                        if self.querying_rules:
                            self._new_rule(act)
                    else:
                        self._new_fact_activations(act)

            self.processing = False
