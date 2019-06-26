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
from typing import List, Dict, Set, Tuple, Any, Optional, cast

from .core import Sentence, Path, Matching
from .sentenceset import SentenceSet
from .util import get_parents


@dataclass(frozen=True)
class Rule:
    conditions : Tuple[Sentence]
    consecuences : Tuple[Sentence]
    varmaps : tuple = field(default_factory=tuple)  # Tuple[Tuple[Sentence, Matching]]

    def get_varmap(self, condition : Sentence) -> Matching:
        for varmap in self.varmaps:
            if condition == varmap[0]:
                break
        return varmap[1]


@dataclass
class ChildNode:
    parent : Optional[ParentNode] = None


@dataclass
class End:
    condition : Sentence
    rules : Set[Rule] = field(default_factory=set)


@dataclass
class EndNode(ChildNode, End):

    def add_matching(self, matching : Matching):
        for rule in self.rules:
            if len(rule.conditions) > 1:
                self.add_new_rule(rule, matching)
            else:
                self.add_new_sentences(rule, matching)

    def add_new_rule(self, rule : Rule, cmatching : Matching):
        rete = get_parents(self)[-1]
        varmap = rule.get_varmap(self.condition)
        matching = cmatching.get_real_matching(varmap)
        conds = tuple(c.substitute(varmap) for c in
                rule.conditions if c != self.condition)
        cons = tuple(c.substitute(varmap) for c in rule.consecuences)
        cons = cast(Tuple[Sentence], cons)
        conds = cast(Tuple[Sentence], conds)
        new_rule = Rule(conds, cons)
        rete.add_rule(new_rule)

    def add_new_sentences(self, rule : Rule, cmatching : Matching):
        rete = get_parents(self)[-1]
        varmap = rule.get_varmap(self.condition)
        matching = cmatching.get_real_matching(varmap)
        cons = [c.substitute(varmap) for c in rule.consecuences]
        rete.pending += cons
        rete.proccess()


@dataclass
class ParentNode:
    var_child : Optional[ParentNode] = None
    children : Dict[Path, ParentNode] = field(default_factory=dict)
    endnode : Optional[EndNode] = None

    def propagate(self, paths : List[Path], matching : Matching):

        visited = get_parents(self)
        if paths:
            path = paths.pop()
            for node in visited:
                if path in node.children:
                    node.children[path].propagate(copy(paths), matching)
                if node.var_child:
                    if node.var_child.value in matching:
                        if matching[node.var_child.value] == path.value:
                            node.var_child.propagate(copy(paths), matching)
                    else:
                        new_matching = matching.setitem(node.var_child.value,
                                                        path.value)
                        node.var_child.propagate(copy(paths), new_matching)

        if self.endnode:
            self.endnode.add_matching(matching)


@dataclass
class ContentNode:
    path : Path
    var : bool


@dataclass
class Node(ParentNode, ChildNode, ContentNode):
    pass


@dataclass
class Rete(ParentNode, ChildNode):
    sset : SentenceSet = field(default_factory=SentenceSet)
    pending : List[Sentence] = field(default_factory=list)
    processing : bool = False

    def add_rule(self, rule):
        varmaps = []
        endnodes = []
        for cond in rule.conditions:
            condition, varmap, paths = cond.normalize()
            varmaps.append((condition, varmap))
            node = self
            paths_left = []
            for i, path in enumerate(paths):
                if path in node.children:
                    node = node.children[path]
                else:
                    paths_left = paths[i:]
                    break
            for path in paths_left:
                next_node = Node(path, path.var, parent=node)
                node.children[path] = next_node
                node = next_node
            if node.endnode is None:
                node.endnode = EndNode(condition=cond, parent=node)
            endnodes.append(node.endnode)
        final_rule = Rule(rule.conditions, rule.consecuences, tuple(varmaps))
        for en in endnodes:
            en.rules.add(final_rule)

    def add_sentence(self, sentence : Sentence):
        paths = sentence.get_paths()
        matching = Matching()
        self.propagate(paths, matching)

    def tell(self, s : Any):
        if isinstance(s, Rule):
            self.add_rule(s)
        elif isinstance(s, Sentence):
            self.pending.append(s)
            self.process()

    def ask(self, q : Sentence) -> Optional[List[Matching]]:
        return self.sset.ask_sentence(q)

    def process(self):
        try:
            if not self.processing:
                self.processing = True
                while self.pending:
                    s = self.pending.pop()
                    if not self.ask(s):
                        self.sset.add_sentence(s)
                        self.add_sentence(s)
        finally:
            self.processing = False

