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

import os.path
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


class KnowledgeBase:
    '''
    The object that contains both the graph of rules (or the tree of
    conditions) and the graph of facts.
    '''
    def __init__(self, grammar_text : str,
                 fact_rule : str = 'fact',
                 var_range_expr : str = '^v_',
                 base_grammar_fn='../grammars/_base.peg',
                 backend : str = 'parsimonious'):
        '''
        '''
        if not os.path.isabs(base_grammar_fn):
            here = os.path.abspath(os.path.dirname(__file__))
            base_grammar_fn = os.path.join(here, base_grammar_fn)
        with open(base_grammar_fn) as fh:
            common = fh.read()
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
            activation = self._deal_with_told_rule_tree(tree)
        elif tree.expr.name == self.fact_rule:
            fact = self.from_parse_tree(tree)
            activation = Activation('fact', fact, data={'query_rules': self.querying_rules})
        elif tree.expr.name == '__rm__':
            fact = self.from_parse_tree(tree.children[2])
            activation = Activation('rm', fact, data={'query_rules': False})
        self.activations.append(activation)
        self.process()

    def _deal_with_told_rule_tree(self, tree : Node) -> Activation:
        for child_node in tree.children:
            if child_node.expr.name == '__conds__':
                conds = tuple(self.from_parse_tree(ch.children[0]) for ch
                              in child_node.children)
            elif child_node.expr.name == '__conss__':
                conss = tuple(self.from_parse_tree(ch.children[0]) for ch
                              in child_node.children)
        rule = Rule(conds, conss)
        act_data = {
            'matching': EMPTY_MATCHING,
            'condition': EMPTY_FACT,
            'query_rules': True
            }
        return Activation('rule', rule, data=act_data)

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
            conds = [c.substitute(bt.data['matching'], self) for c in
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
        matching = act.data['matching']
        conds = [c.substitute(matching, self) for c in
                rule.conditions if c != act.data['condition']]
        new_conds = tuple(conds)
        cons = tuple(c.substitute(matching, self) for c in rule.consecuences)
        new_rule = Rule(new_conds, cons)
        self.dset.add_rule(new_rule)
        self.sset.add_rule(new_rule)
        return new_rule

    def _new_fact_activations(self, act : Activation):
        rule = cast(Rule, act.precedent)
        matching = act.data['matching']
        cons = tuple(c.substitute(matching, self) for c in rule.consecuences)
        act_data = {'query_rules': self.querying_rules}
        acts = [Activation('fact', c, data=act_data) for c in cons]
        self.activations.extend(acts)

    def _new_rule(self, rule : Rule):
        for cond in rule.conditions:
            answers = self.fset.ask_fact(cond)
            for a in answers:
                rulestr = str(rule) + str(a) + str(cond)
                if rulestr in self.seen_rules:
                    continue
                self.seen_rules.add(rulestr)
                act_data = {
                    'matching': a,
                    'condition': cond,
                    'query_rules': True
                    }
                act = Activation('rule', rule, data=act_data)
                self.activations.append(act)

    def _new_facts(self, act : Activation):
        rule = cast(Rule, act.precedent)
        for cond in rule.conditions:
            answers = self.fset.ask_fact(cond)
            for a in answers:
                rulestr = str(rule) + str(a) + str(cond)
                if rulestr in self.seen_rules:
                    continue
                self.seen_rules.add(rulestr)
                act_data = {
                    'matching': a,
                    'condition': cond,
                    'query_rules': True
                    }
                act = Activation('rule', rule, data=act_data)
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
                self.querying_rules = bool(act.data.get('query_rules'))
                self.counter += 1
                s = act.precedent
                if act.kind == 'fact':
                    if not self.ask(s):
                        logger.info(f'adding fact "{s}"')
                        self._add_fact(s)
                        self.fset.add_fact(s)
                elif act.kind == 'rule':
                    if len(s.conditions) > 1 or act.data['condition'] == EMPTY_FACT:
                        new_rule = self._new_rule_activation(act)
                        logger.info(f'adding rule "{new_rule}"')
                        if self.querying_rules:
                            self._new_rule(new_rule)
                    else:
                        self._new_fact_activations(act)
                        if self.querying_rules:
                            self._new_facts(act)
                elif act.kind == 'rm':
                    logger.info(f'removing fact "{s}"')
                    self.fset.rm_fact(s, self)
                    # XXX we must also remove the rules createdf by this fact -
                    # for which we must keep track of the originated rules in
                    # each fact - and of the endnodes that point to them in
                    # each rule, so we can remove the rules and the endnodes
                    # that contain only the rules and any parent node that may
                    # be left childless and with an empty endnode.

                    # or - only allow certain conditions to produce activations
                    # for facts and not for rules - non-logical conditions that
                    # are actually logical

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
