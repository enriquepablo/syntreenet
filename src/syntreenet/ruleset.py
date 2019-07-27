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

from .grammar import Segment, Fact, Path, Matching
from .factset import FactSet


@dataclass(frozen=True)
class Rule:
    '''
    A rule. A set of conditions plus a set of consecuences.
    '''
    conditions : tuple = field(default_factory=tuple)
    extra_conditions : tuple = field(default_factory=tuple)
    consecuences : tuple = field(default_factory=tuple)
    to_remove : tuple = field(default_factory=tuple)
    extra_matching : Optional[Matching] = None

    def __str__(self) -> str:
        conds = '; '.join([str(c) for c in self.conditions])
        econds = '; '.join([str(c) for c in self.extra_conditions])
        if econds:
            econds = '; ' + econds
        cons = '; '.join([str(c) for c in self.consecuences])
        rms = '; '.join([str(c) for c in self.to_remove])
        if rms:
            cons = f'{rms} ; {cons}'
        return f'{conds} {econds} -> {cons}'


@dataclass(frozen=True)
class ExtraCondition:
    kind : str
    text : str


@dataclass
class ChildNode:
    parent : Optional[ParentNode] = None


@dataclass(frozen=True)
class Activation:
    '''
    An activation is produced when a fact matches a condition in a rule,
    and contains the information needed to produce the new facts or rules.
    '''
    kind : str
    precedent : Union[Rule, Fact]
    data : Dict[str, Any] = field(default_factory=dict)


@dataclass
class End:
    continuations : Dict[str, Tuple[Fact, Matching, Rule]] = field(default_factory=dict)


def get_root(node):
    while node.parent is not None:
        node = node.parent
    return node


@dataclass
class EndNode(ChildNode, End):
    '''
    An endnode marks its parent node as a node corresponding to some
    condition(s) in some rule(s).
    It contains information about the rules that have this condition, and the
    mapping of the (normalized) variables in the condition in the ruleset, to
    the actual variables in the rule provided by the user.
    '''
    parent : Optional[ParentNode] = None
    kb : Any = None

    def add_matching(self, matching : Matching):
        '''
        '''
        root = get_root(self)
        for condition, varmap, rule in self.continuations.values():
            real_matching = matching.get_real_matching(varmap)
            act_data = {
                    'matching': real_matching,
                    'condition': condition,
                    'query_rules': self.kb.querying_rules
                    }
            activation = Activation('rule', rule, data=act_data)
            root.add_activation(activation)


@dataclass
class ParentNode:
    '''
    '''
    var_child : Optional[Node] = None
    var_children : List[Node] = field(default_factory=list)
    children : Dict[Path, Node] = field(default_factory=dict)
    endnode : Optional[EndNode] = None

    def propagate(self, paths : List[Path], matching : Matching):
        '''
        '''
        if paths:
            path = paths.pop(0)
            child = self.children.get(path)
            if child is not None:
                child.propagate(copy(paths), matching)
            
            for vchild in self.var_children:
                new_path = path.get_subpath(vchild.path)
                if new_path.value == matching[vchild.path.value]:
                    new_paths = new_path.paths_after(paths, try_to_see=False)
                    vchild.propagate(new_paths, matching)
                    break

            if self.var_child is not None:
                new_path = path.get_subpath(self.var_child.path)
                new_paths = new_path.paths_after(paths, try_to_see=False)
                child_var = self.var_child.path.value
                new_matching = matching.setitem(child_var, new_path.value)
                self.var_child.propagate(new_paths, new_matching)

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
    parent : ParentNode


@dataclass
class RuleSet(ParentNode, ChildNode):
    kb : Any = None

    def follow_paths(self, paths : List[Path]) -> Tuple[ParentNode,
                                                        List[Segment],
                                                        List[Path]]:
        node : ParentNode = self
        visited_vars = []
        rest_paths : List[Path] = []
        for i, path in enumerate(paths):
            if path.is_var():
                var_child = None
                for ch in node.var_children:
                    if ch.path == path:
                        var_child = ch
                        break
                if var_child is not None:
                    node = var_child
                elif node.var_child and path == node.var_child.path:
                    visited_vars.append(path.value)
                    node = node.var_child
                else:
                    rest_paths = paths[i:]
                    break
            else:
                child = node.children.get(path)
                if child:
                    node = child
                else:
                    rest_paths = paths[i:]
                    break
        return node, visited_vars, rest_paths

    def create_paths(self, node : ParentNode,
                     paths : List[Path], visited : List[Segment]) -> Node:
        for path in paths:
            next_node = Node(path, path.is_var(), parent=node)
            if path.is_var():
                if path.value not in visited:
                    visited.append(path.value)
                    node.var_child = next_node
                else:
                    node.var_children.append(next_node)
            else:
                node.children[path] = next_node
            node = next_node

        return cast(Node, node)

    def add_rule(self, rule : Rule):
        '''
        '''
        for con in self.get_cons(rule):
            varmap, paths = con.normalize(self.kb)
            node, visited_vars, paths_left = self.follow_paths(paths)
            node = self.create_paths(node, paths_left, visited_vars)
            if node.endnode is None:
                node.endnode = EndNode(parent=node, kb=self.kb)
            rulestr = str(rule) + str(varmap) + str(con)
            if rulestr not in node.endnode.continuations:
                node.endnode.continuations[rulestr] = (con, varmap, rule)

    def get_cons(self, rule : Optional[Rule]) -> tuple:
        raise NotImplementedError()

    def add_activation(self, act : Optional[Activation]):
        raise NotImplementedError()


@dataclass
class CondSet(RuleSet):

    def get_cons(self, rule):
        return rule.conditions

    def add_activation(self, act):
        self.kb.activations.append(act)


@dataclass
class ConsSet(RuleSet):
    backtracks : List[Activation] = field(default_factory=list)

    def get_cons(self, rule):
        return rule.consecuences

    def add_activation(self, act):
        self.backtracks.append(act)
