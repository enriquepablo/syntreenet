# Copyright (c) 2019 by Enrique Pérez Arnaud <enrique@cazalla.net>
#
# This file is part of the whatever project.
# https://whatever.cazalla.net
#
# The whatever project is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# The whatever project is distributed in the hope that it will be useful,
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
from typing import List, Dict, Union, Tuple, Any, Optional, cast

from .core import Syntagm, Fact, Path, Matching
from .factset import FactSet
from .util import get_parents
from .logging import logger


@dataclass(frozen=True)
class Rule:
    '''
    A rule. A set of conditions plus a set of consecuences.
    '''
    conditions : tuple = field(default_factory=tuple)
    consecuences : tuple = field(default_factory=tuple)
    empty_matching : Matching = Matching()

    def __str__(self):
        conds = '; '.join([str(c) for c in self.conditions])
        cons = '; '.join([str(c) for c in self.consecuences])
        return f'{conds} -> {cons}'


@dataclass
class ChildNode:
    parent : Optional[ParentNode] = None


@dataclass(frozen=True)
class Activation:
    '''
    An activation is produced when a fact matches a condition in a rule,
    and contains the information needed to produce the new facts or rules.
    '''
    precedent : Union[Rule, Fact]
    matching : Optional[Matching] = None
    condition : Optional[Fact] = None


@dataclass
class End:
    conditions : List[Tuple[Fact, Matching, Rule]] = field(default_factory=list)


@dataclass
class EndNode(ChildNode, End):
    '''
    An endnode marks its parent node as a node corresponding to some
    condition(s) in some rule(s).
    It contains information about the rules that have this condition, and the
    mapping of the (normalized) variables in the condition in the ruleset, to
    the actual variables in the rule provided by the user.
    '''

    def __str__(self):
        return f'end for : {self.parent}'

    def add_matching(self, matching : Matching):
        '''
        This is called when a new fact matches all nodes leading to a node
        with self as endnode.
        matching contains the variable assignment that equates the condition
        and the new fact.
        '''
        rete = get_parents(self)[-1]
        for condition, varmap, rule in self.conditions:
            real_matching = matching.get_real_matching(varmap)
            activation = Activation(rule, real_matching, condition)
            rete.activations.append(activation)
        rete.process()


@dataclass
class ParentNode:
    '''
    A parent node in the tree of conditions.
    children contains a mapping of paths to non-variable child nodes.
    var_child points to a variable child node, if the variable appears for the
    1st time in the condition.
    var_children contains a mapping of paths to variable child nodes, if the
    variable has already appeared in the current branch.
    endnode points to an EndNode, in case this ParentNode corresponds with the
    last path in a condition.

    Both Node and KnowledgeBase are ParentNodes
    '''
    var_child : Optional[Node] = None
    var_children : Dict[Path, Node] = field(default_factory=dict)
    children : Dict[Path, Node] = field(default_factory=dict)
    endnode : Optional[EndNode] = None

    def propagate(self, paths : List[Path], matching : Matching, first : bool = False):
        '''
        Find the conditions that the fact represented by the paths in paths
        matches, recursively.
        Accumulate variable assignments in matching.
        '''
        visited = get_parents(self)
        if paths:
            path = paths.pop(0)
            # AA FR 03 - Algorithmic Analysis - Checking a Fact with the RuleSet
            # AA FR 03 - visited contains all the parents of the current node
            # up to the root node, and can_follow should weed ut most of them;
            # this is something that depends on the internal complexity of the
            # conditions.
            for node in visited:
                if hasattr(node, 'path'):
                    if not path.can_follow(node.path):
                        continue
                elif not first:
                    continue
                child = node.children.get(path)
                if child is not None:
                    child.propagate(copy(paths), matching.copy())
                var : Optional[Syntagm] = matching.getkey(path.value)
                if var is not None:
                    new_path = path.change_value(var)
                    var_child = node.var_children.get(new_path)
                    if var_child is not None:
                        new_paths = [p.change_subpath(new_path, path.value) for p in paths]
                        var_child.propagate(new_paths, matching.copy())
                if node.var_child is not None:
                    child_var = node.var_child.path.value
                    old_value = path.value
                    new_matching = matching.setitem(child_var, old_value)
                    new_path = path.change_value(child_var)
                    new_paths = [p.change_subpath(new_path, old_value) for p in paths]
                    node.var_child.propagate(new_paths, new_matching)

        if self.endnode:
            self.endnode.add_matching(matching)


@dataclass
class ContentNode:
    '''
    A node that corresponds to a path in one or more conditions of rules.

    Node is the only ContentNode (which is needed only to order correctly the
    attributes in Node).
    '''
    path : Path
    var : bool


@dataclass
class Node(ParentNode, ChildNode, ContentNode):
    '''
    A node in the tree of conditions.
    '''

    def __str__(self):
        return f'node : {self.path}'


@dataclass
class KnowledgeBase(ParentNode, ChildNode):
    '''
    The object that contains both the graph of rules (or the tree of
    conditions) and the graph of facts.
    '''
    fset : FactSet = field(default_factory=FactSet)
    activations : List[Activation] = field(default_factory=list)
    processing : bool = False
    counter : int = 0
    _empty_matching : Matching = Matching()
    _empty_fact : Fact = Fact()

    def __str__(self):
        return 'rete root'

    def tell(self, s : Any):
        '''
        Add new sentence (rule or fact) to the knowledge base.
        '''
        if isinstance(s, Rule):
            activation = Activation(s, self._empty_matching, self._empty_fact)
        elif isinstance(s, Fact):
            activation = Activation(s)
        self.activations.append(activation)
        self.process()

    def ask(self, q : Fact) -> Optional[List[Matching]]:
        '''
        Check whether a fact exists in the knowledge base, or, if it contains
        variables, find all the variable assigments that correspond to facts
        that exist in the knowledge base.
        '''
        return self.fset.ask_fact(q)

    def add_rule(self, rule):
        '''
        This method is the entry to the agorithm to add new rules to the knowledge
        base.
        '''
        logger.info(f'adding rule "{rule}"')
        endnodes = []
        # AA AR 01 - Algorithmic Analysis - Adding a Rule
        # AA AR 01 - For each rule we process its conditions sequentially.
        # AA AR 01 - This provides a linear dependence to processing a rule on the
        # AA AR 01 - number of conditions it holds.
        # AA AR 01 - wrt the size of the kb, this is O(1)
        for cond in rule.conditions:
            # AA AR 02 - Algorithmic Analysis - Adding a rule
            # AA AR 02 - normalize will visit all segments in all paths corresponding
            # AA AR 02 - to a condition. This only depends on the complexity of
            # AA AR 02 - the condition.
            # AA AR 02 - wrt the size of the kb, this is O(1)
            varmap, paths = cond.normalize()
            # AA AR 03 - Algorithmic Analysis - Adding a rule
            # AA AR 03 - We continue the analisis whithin _follow_paths
            node, visited_vars, paths_left = self._follow_paths(paths)
            # AA AR 08 - Algorithmic Analysis - Adding a rule
            # AA AR 08 - We continue the analisis whithin _create_paths
            node = self._create_paths(node, paths_left, visited_vars)
            # AA AR 11 - Algorithmic Analysis - the rest of the operations from here on only operate on
            # AA AR 11 - the information provided in the condition,
            # AA AR 11 - and therefore are O(1) wrt the size of the kb.
            if node.endnode is None:
                node.endnode = EndNode(parent=node)
            node.endnode.conditions.append((cond, varmap, rule))

    def _follow_paths(self, paths : List[Path]) -> Tuple[ParentNode, List[Syntagm], List[Path]]:
        node : ParentNode = self
        visited_vars = []
        rest_paths : List[Path] = []
        # AA AR 04 - Algorithmic Analysis - Adding a rule
        # AA AR 04 - we iterate over the paths that correspond to a condition.
        # AA AR 04 - This only depends on the complexity of the condition.
        # AA AR 04 - wrt the size of the kb, this is O(1)
        for i, path in enumerate(paths):
            if path.var:
                # AA AR 05 - Algorithmic Analysis - Adding a Rule
                # AA AR 05 - Here we consult a hash table with, at most, 1 less
                # AA AR 05 - entries than the number of variables in the condition
                # AA AR 05 - it corrsponds to.
                # AA AR 05 - So this depends only on the complexity of the
                # AA AR 05 - condition.
                # AA AR 05 - wrt the size of the kb, this is O(1)
                var_child = node.var_children.get(path)
                if var_child is not None:
                    node = var_child
                elif node.var_child and path.value == node.var_child.path.value:
                    visited_vars.append(path.value)
                    node = node.var_child
                else:
                    rest_paths = paths[i:]
                    break
            # AA AR 06 - Algorithmic Analysis - Adding a Rule
            # AA AR 06 - Here we consult a hash table with a number of
            # AA AR 06 - children that is proportional to both the complexity of the
            # AA AR 06 - conditions and to the size of the kb.
            # AA AR 06 - so wrt the size of the kb, this is at worst
            # AA AR 06 - O(log(n))
            elif path in node.children:
                node = node.children[path]
            else:
                rest_paths = paths[i:]
                break
        return node, visited_vars, rest_paths

    def _create_paths(self, node : ParentNode, paths : List[Path], visited : List[Syntagm]) -> Node:
        # AA AR 09 - Algorithmic Analysis - Adding a rule
        # AA AR 09 - we iterate over the paths that correspond to a condition.
        # AA AR 09 - This only depends on the complexity of the condition.
        # AA AR 09 - wrt the size of the kb, this is O(1)
        for path in paths:
            # AA AR 10 - Algorithmic Analysis - Adding a rule
            # AA AR 10 - the rest of the operations from here on only operate on
            # AA AR 10 - the information provided in the condition,
            # AA AR 10 - and therefore are O(1) wrt the size of the kb.
            next_node = Node(path, path.var, parent=node)
            if path.var:
                if path.value not in visited:
                    visited.append(path.value)
                    node.var_child = next_node
                    node = next_node
                else:
                    node.var_children[path] = next_node
                    node = next_node
            else:
                node.children[path] = next_node
                node = next_node
        return cast(Node, node)

    def add_fact(self, fact : Fact):
        '''
        This method is the entry to the algorithm that checks for conditions
        that match a new fact being added to the knowledge base. 
        '''
        # AA FR 01 - Algorithmic Analysis - Checking a Fact with the RuleSet
        logger.debug(f'adding fact "{fact}" to rete')
        paths = fact.get_paths()
        matching = Matching()
        # AA FR 02 - Algorithmic Analysis - Checking a Fact with the RuleSet
        # AA FR 02 - We continue the analisis whithin propagate
        self.propagate(paths, matching, first=True)

    def add_new_rule(self, act : Activation):
        rule = cast(Rule, act.precedent)
        conds = tuple(c.substitute(act.matching) for c in
                rule.conditions if c != act.condition)
        cons = tuple(c.substitute(act.matching) for c in rule.consecuences)
        cons = cast(Tuple[Fact], cons)
        conds = cast(Tuple[Fact], conds)
        new_rule = Rule(conds, cons)
        self.add_rule(new_rule)

    def add_new_facts(self, act : Activation):
        rule = cast(Rule, act.precedent)
        cons = tuple(c.substitute(act.matching) for c in rule.consecuences)
        acts = [Activation(c) for c in cons]
        self.activations.extend(acts)
        self.process()

    def process(self):
        '''
        Process all pending activations, and add the corresponding sentences to
        the knowledge base.
        '''
        if not self.processing:
            self.processing = True
            while self.activations:
                act = self.activations.pop(0)
                self.counter += 1
                s = act.precedent
                if isinstance(s, Fact):
                    if not self.ask(s):
                        logger.info(f'adding fact "{s}"')
                        self.add_fact(s)
                        self.fset.add_fact(s)
                elif isinstance(s, Rule):
                    if len(s.conditions) > 1:
                        self.add_new_rule(act)
                    else:
                        self.add_new_facts(act)

            self.processing = False
