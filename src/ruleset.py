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
        # AA FR 10 0 - Algorithmic Analysis - Checking a Fact with the RuleSet
        # AA FR 10 1 - Here we recurse over all the rules that have the condition
        # AA FR 10 2 - that has been matched. This add a linear dependency on the number of
        # AA FR 10 3 - consecuences to the complexity of adding a fact with all its
        # AA FR 10 4 - consecuences.
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

    def propagate(self, paths : List[Path], matching : Matching):
        '''
        Find the conditions that the fact represented by the paths in paths
        matches, recursively.
        Accumulate variable assignments in matching.
        '''
        visited = get_parents(self)
        if paths:
            path = paths.pop(0)
            # AA FR 03 0 - Algorithmic Analysis - Checking a Fact with the RuleSet
            # AA FR 03 1 - visited contains all the parents of the current node
            # AA FR 03 2 - up to the root node, and can_follow should weed ut most of them;
            # AA FR 03 3 - this is something that depends on the internal complexity of the
            # AA FR 03 4 - conditions.
            for node in visited:
                if hasattr(node, 'path'):
                    if not path.can_follow(node.path):
                        continue
                elif not path.can_be_first():
                    continue
                # AA FR 04 0 - Algorithmic Analysis - Checking a Fact with the RuleSet
                # AA FR 04 1 - Here we consult a hash table. This add a
                # AA FR 04 2 - logarithmic dependency on the number of child nodes - on the
                # AA FR 04 3 - size of the kb.
                child = node.children.get(path)
                if child is not None:
                    # AA FR 05 0 - Algorithmic Analysis - Checking a Fact with the RuleSet
                    # AA FR 05 1 - Recurse though child nodes. The cost of each
                    # AA FR 05 2 - step is logarithmic wrt the size of the kb, as we've seen
                    # AA FR 05 3 - above, and the depth of recursion reached here does not
                    # AA FR 05 4 - depend on the size of the kb, but on the provided grammar.
                    child.propagate(copy(paths), matching.copy())
                var : Optional[Syntagm] = matching.getkey(path.value)
                if var is not None:
                    new_path = path.change_value(var)
                    # AA FR 06 0 - Algorithmic Analysis - Checking a Fact with the RuleSet
                    # AA FR 06 1 - Here we consult a hash table with very few
                    # AA FR 06 2 - elements - at most the one less y than the number of
                    # AA FR 06 3 - variables in the conditions it takes part of - so it
                    # AA FR 06 4 - depends on the grammar (and should not be a dict).
                    var_child = node.var_children.get(new_path)
                    if var_child is not None:
                        new_paths = [p.change_subpath(new_path, path.value) for p in paths]
                        # AA FR 07 0 - Algorithmic Analysis - Checking a Fact with the RuleSet
                        # AA FR 07 1 - The same as (AA FR 05)
                        var_child.propagate(new_paths, matching.copy())
                if node.var_child is not None:
                    child_var = node.var_child.path.value
                    old_value = path.value
                    new_matching = matching.setitem(child_var, old_value)
                    new_path = path.change_value(child_var)
                    new_paths = [p.change_subpath(new_path, old_value) for p in paths]
                    # AA FR 08 0 - Algorithmic Analysis - Checking a Fact with the RuleSet
                    # AA FR 08 1 - The same as (AA FR 05)
                    node.var_child.propagate(new_paths, new_matching)

        if self.endnode:
            # AA FR 09 0 - Algorithmic Analysis - Checking a Fact with the RuleSet
            # AA FR 09 1 - Continue analysis in add_matching
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

    def _add_rule(self, rule):
        '''
        This method is the entry to the agorithm to add new rules to the knowledge
        base.
        '''
        logger.info(f'adding rule "{rule}"')
        endnodes = []
        # AA AR 01 0 - Algorithmic Analysis - Adding a Rule
        # AA AR 01 1 - For each rule we process its conditions sequentially.
        # AA AR 01 2 - This provides a linear dependence to processing a rule on the
        # AA AR 01 3 - number of conditions it holds.
        # AA AR 01 4 - wrt the size of the kb, this is O(1)
        for cond in rule.conditions:
            # AA AR 02 0 - Algorithmic Analysis - Adding a rule
            # AA AR 02 1 - normalize will visit all segments in all paths corresponding
            # AA AR 02 2 - to a condition. This only depends on the complexity of
            # AA AR 02 3 - the condition.
            # AA AR 02 4 - wrt the size of the kb, this is O(1)
            varmap, paths = cond.normalize()
            # AA AR 03 0 - Algorithmic Analysis - Adding a rule
            # AA AR 03 1 - We continue the analisis whithin _follow_paths
            node, visited_vars, paths_left = self._follow_paths(paths)
            # AA AR 08 0 - Algorithmic Analysis - Adding a rule
            # AA AR 08 1 - We continue the analisis whithin _create_paths
            node = self._create_paths(node, paths_left, visited_vars)
            # AA AR 11 0 - Algorithmic Analysis - the rest of the operations from here on
            # AA AR 11 1 - only operate on the information provided in the condition,
            # AA AR 11 2 - and therefore are O(1) wrt the size of the kb.
            if node.endnode is None:
                node.endnode = EndNode(parent=node)
            node.endnode.conditions.append((cond, varmap, rule))

    def _follow_paths(self, paths : List[Path]) -> Tuple[ParentNode, List[Syntagm], List[Path]]:
        node : ParentNode = self
        visited_vars = []
        rest_paths : List[Path] = []
        # AA AR 04 0 - Algorithmic Analysis - Adding a rule
        # AA AR 04 1 - we iterate over the paths that correspond to a condition.
        # AA AR 04 2 - This only depends on the complexity of the condition.
        # AA AR 04 3 - wrt the size of the kb, this is O(1)
        for i, path in enumerate(paths):
            if path.var:
                # AA AR 05 0 - Algorithmic Analysis - Adding a Rule
                # AA AR 05 1 - Here we consult a hash table with, at most, 1 less
                # AA AR 05 2 - entries than the number of variables in the condition
                # AA AR 05 3 - it corrsponds to.
                # AA AR 05 4 - So this depends only on the complexity of the
                # AA AR 05 5 - condition.
                # AA AR 05 6 - wrt the size of the kb, this is O(1)
                var_child = node.var_children.get(path)
                if var_child is not None:
                    node = var_child
                elif node.var_child and path.value == node.var_child.path.value:
                    visited_vars.append(path.value)
                    node = node.var_child
                else:
                    rest_paths = paths[i:]
                    break
            else:
                # AA AR 06 0 - Algorithmic Analysis - Adding a Rule
                # AA AR 06 1 - Here we consult a hash table with a number of
                # AA AR 06 2 - children that is proportional to both the complexity of the
                # AA AR 06 3 - conditions and to the size of the kb.
                # AA AR 06 4 - so wrt the size of the kb, this is at worst
                # AA AR 06 5 - O(log n)
                child = node.children.get(path)
                if child:
                    node = child
                else:
                    rest_paths = paths[i:]
                    break
        return node, visited_vars, rest_paths

    def _create_paths(self, node : ParentNode, paths : List[Path], visited : List[Syntagm]) -> Node:
        # AA AR 09 0 - Algorithmic Analysis - Adding a rule
        # AA AR 09 1 - we iterate over the paths that correspond to a condition.
        # AA AR 09 2 - This only depends on the complexity of the condition.
        # AA AR 09 3 - wrt the size of the kb, this is O(1)
        for path in paths:
            # AA AR 10 0 - Algorithmic Analysis - Adding a rule
            # AA AR 10 1 - the rest of the operations from here on only operate on
            # AA AR 10 2 - the information provided in the condition,
            # AA AR 10 3 - and therefore are O(1) wrt the size of the kb.
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

    def _add_fact(self, fact : Fact):
        '''
        This method is the entry to the algorithm that checks for conditions
        that match a new fact being added to the knowledge base. 
        '''
        # AA FR 01 0 - Algorithmic Analysis - Checking a Fact with the RuleSet
        logger.debug(f'adding fact "{fact}" to rete')
        paths = fact.get_paths()
        matching = Matching()
        # AA FR 02 0 - Algorithmic Analysis - Checking a Fact with the RuleSet
        # AA FR 02 1 - We continue the analisis whithin propagate
        self.propagate(paths, matching)

    def _add_new_rule(self, act : Activation):
        rule = cast(Rule, act.precedent)
        conds = tuple(c.substitute(act.matching) for c in
                rule.conditions if c != act.condition)
        cons = tuple(c.substitute(act.matching) for c in rule.consecuences)
        cons = cast(Tuple[Fact], cons)
        conds = cast(Tuple[Fact], conds)
        new_rule = Rule(conds, cons)
        self._add_rule(new_rule)

    def _add_new_facts(self, act : Activation):
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
                        self._add_fact(s)
                        self.fset.add_fact(s)
                elif isinstance(s, Rule):
                    if len(s.conditions) > 1:
                        self._add_new_rule(act)
                    else:
                        self._add_new_facts(act)

            self.processing = False
