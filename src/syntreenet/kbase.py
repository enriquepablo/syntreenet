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
from dataclasses import dataclass, field
from typing import List, Set, Union, cast

from .grammar import Segment, Path, Fact, Matching
from .factset import FactSet
from .ruleset import CondSet, ConsSet, Activation, Rule, ExtraCondition
from .extra import ec_handlers
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
        return bool(self.var_range_expr.match(path[-1].name))

    def tell(self, s : str):
        '''
        Add new sentence (rule or fact) to the knowledge base.
        '''
        tree = self.parse(s)
        if tree.expr.name == '__rule__':
            activation = self._deal_with_told_rule_tree(tree)
        elif tree.expr.name == self.fact_rule:
            fact = self.from_parse_tree(tree)
            activation = Activation('fact', fact, data={'query_rules': False})
        elif tree.expr.name == '__rm__':
            fact = self.from_parse_tree(tree.children[2])
            activation = Activation('rm', fact, data={'query_rules': False})
        self.activations.append(activation)
        self.process()

    def _deal_with_told_rule_tree(self, tree : Node) -> Activation:
        econds : tuple = ()
        for child_node in tree.children:
            if child_node.expr.name == '__conds__':
                conds = tuple(self.from_parse_tree(ch.children[0]) for ch
                              in child_node.children)
            elif child_node.expr.name == '__econds__':
                econds = tuple(ExtraCondition(kind=ch.children[0].children[2].text,
                                              text=ch.children[0].children[4].text)
                               for ch in child_node.children)
            elif child_node.expr.name == '__conss__':
                conss_list = []
                rms_list = []
                for child in child_node.children:
                    if child.children[0].children[0].expr.name == self.fact_rule:
                        conss_list.append(self.from_parse_tree(child.children[0].children[0]))
                    elif child.children[0].children[0].expr.name == "__rm__":
                        fact_tree = child.children[0].children[0].children[2]
                        rms_list.append(self.from_parse_tree(fact_tree))
                    pass
                conss = tuple(conss_list)
                rms = tuple(rms_list)
        rule = Rule(conds, econds, conss, rms)
        act_data = {
            'matching': EMPTY_MATCHING,
            'condition': EMPTY_FACT,
            'query_rules': True
            }
        return Activation('rule', rule, data=act_data)

    def query(self, q : str) -> Union[dict, bool]:
        tree = self.parse(q)
        qf = self.from_parse_tree(tree)
        response = self.ask(qf)
        if not response:
            return False
        if len(response) == 1 and not response[0].mapping:
            return True
        return [m.to_dict() for m in response]

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
        rms = tuple(c.substitute(matching, self) for c in rule.to_remove)
        econds = rule.extra_conditions
        new_extra_matching = None
        if rule.extra_conditions:
            if rule.extra_matching is None:
                new_extra_matching = matching
            else:
                new_extra_matching = matching.merge(rule.extra_matching)
        new_rule = Rule(new_conds, econds, cons, rms, new_extra_matching)
        self.dset.add_rule(new_rule)
        self.sset.add_rule(new_rule)
        return new_rule

    def _new_fact_activations(self, act : Activation):
        rule = cast(Rule, act.precedent)
        matching = act.data['matching']
        all_results = [matching.merge(rule.extra_matching)]
        prev_results = []
        for ec in rule.extra_conditions:
            for m in all_results:
                results = getattr(ec_handlers, ec.kind)(ec.text, m, self)
                if results is True:
                    continue
                elif results is False:
                    return
                new_results = []
                for pm in results:
                    new_results.append(m.merge(pm))
                if new_results:
                    prev_results.extend(new_results)

            if prev_results:
                all_results = prev_results
                prev_results = []

        for m in all_results:
            self._new_fact_activation(rule, m)

    def _new_fact_activation(self, rule : Rule, matching : Matching):
        act_data = {'query_rules': self.querying_rules}
        for c in rule.to_remove:
            kind = 'rm'
            con = c.substitute(matching, self)
            act = Activation(kind, con, data=act_data)
            self.activations.append(act)
        for c in rule.consecuences:
            kind = 'fact'
            con = c.substitute(matching, self)
            act = Activation(kind, con, data=act_data)
            self.activations.append(act)

    def _new_rule(self, rule : Rule):
        for cond in rule.conditions:
            answers = self.fset.ask_fact(cond)
            for a in answers:
                rulestr = str(rule) + str(a) + str(cond)
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
        name = node.expr.name
        text = node.full_text[node.start: node.end]
        try:
            start = node.start - cast(Segment, parent).start
            end = node.end - cast(Segment, parent).start
        except AttributeError:  # node is root node
            start, end = 0, len(text)
        segment = Segment(text, name, start, end, not bool(node.children))
        path = root_path + (segment,)
        if path[-1].leaf or self.in_var_range(path):
            all_paths.append(path)
        for child in node.children:
            self._visit_pnode(child, path, all_paths, parent=node)
