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

from .core import Syntagm, Sentence, Path, Matching
from .sentenceset import SentenceSet
from .util import get_parents
from .logging import logger


@dataclass(frozen=True)
class Rule:
    conditions : tuple
    consecuences : tuple
    varmaps : tuple = field(default_factory=tuple)  # Tuple[Tuple[Sentence, Matching]]

    def __str__(self):
        conds = ';\n'.join([str(c) for c in self.conditions])
        cons = ';\n'.join([str(c) for c in self.consecuences])
        return f'{conds}\n->\n{cons}'


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
    rules : List[Rule] = field(default_factory=list)


@dataclass
class EndNode(ChildNode, End):

    def __str__(self):
        return f'end for : {self.condition}'

    def add_matching(self, matching : Matching):
        rete = get_parents(self)[-1]
        for rule in self.rules:
            if len(rule.conditions) > 1:
                rete.add_new_rule(rule, self.condition, matching)
            else:
                rete.add_new_sentences(rule, matching)


@dataclass
class ParentNode:
    var_child : Optional[ParentNode] = None
    var_children : Dict[Path, ParentNode] = field(default_factory=dict)
    children : Dict[Path, ParentNode] = field(default_factory=dict)
    endnode : Optional[EndNode] = None

    def propagate(self, paths : List[Path], matching : Matching):
        visited = get_parents(self)
        if paths:
            path = paths.pop()
            for node in visited:
                if hasattr(node, 'path') and not path.can_follow(node.path):
                    continue
                if path in node.children:
                    node.children[path].propagate(copy(paths), matching.copy())
                var = cast(Syntagm, matching.getkey(path.value))
                if var:
                    new_path = path.change_value(var)
                    if new_path in node.var_children:
                        new_paths = [p.change_subpath(new_path, path.value) for p in paths]
                        node.var_children[new_path].propagate(new_paths, matching.copy())
                if node.var_child:
                    var = node.var_child.path.value
                    old_value = path.value
                    new_matching = matching.setitem(var, old_value)
                    new_path = path.change_value(var)
                    new_paths = [p.change_subpath(new_path, old_value) for p in paths]
                    node.var_child.propagate(new_paths, new_matching)

        if self.endnode:
            self.endnode.add_matching(matching)


@dataclass
class ContentNode:
    path : Path
    var : bool


@dataclass
class Node(ParentNode, ChildNode, ContentNode):

    def __str__(self):
        return f'node : {self.path}'


@dataclass
class Rete(ParentNode, ChildNode):
    sset : SentenceSet = field(default_factory=SentenceSet)
    pending : List[Sentence] = field(default_factory=list)
    processing : bool = False

    def __str__(self):
        return 'rete root'

    def tell(self, s : Any):
        if isinstance(s, Rule):
            self.add_rule(s)
        elif isinstance(s, Sentence):
            self.pending.append(s)
            self.process()

    def ask(self, q : Sentence) -> Optional[List[Matching]]:
        return self.sset.ask_sentence(q)

    def add_rule(self, rule):
        logger.info(f'adding rule\n{rule}')
        varmaps = []
        endnodes = []
        for cond in rule.conditions:
            condition, varmap, paths = cond.normalize()
            varmaps.append((condition, varmap))
            node = self
            paths_left = []
            visited_vars = []
            for i, path in enumerate(paths):
                if path.var:
                    if path in node.var_children:
                            node = node.var_children[path]
                    elif node.var_child and path.value == node.var_child.path.value:
                        visited_vars.append(path.value)
                        node = node.var_child
                    else:
                        paths_left = paths[i:]
                        break
                elif path in node.children:
                    node = node.children[path]
                else:
                    paths_left = paths[i:]
                    break
            for path in paths_left:
                next_node = Node(path, path.var, parent=node)
                if path.var:
                    if path.value not in visited_vars:
                        visited_vars.append(path.value)
                        node.var_child = next_node
                        node = next_node
                    else:
                        node.var_children[path] = next_node
                        node = next_node
                else:
                    node.children[path] = next_node
                    node = next_node
            if node.endnode is None:
                node.endnode = EndNode(condition=cond, parent=node)
            endnodes.append(node.endnode)
        final_rule = Rule(rule.conditions, rule.consecuences, tuple(varmaps))
        for endnode in endnodes:
            endnode.rules.append(final_rule)

    def add_sentence(self, sentence : Sentence):
        logger.debug(f'adding sentence "{sentence}" to rete')
        paths = sentence.get_paths()
        paths.reverse()
        matching = Matching()
        self.propagate(paths, matching)

    def add_new_rule(self, rule : Rule, condition : Sentence, matching : Matching):
        conds = tuple(c.substitute(matching) for c in
                rule.conditions if c != condition)
        cons = tuple(c.substitute(matching) for c in rule.consecuences)
        cons = cast(Tuple[Sentence], cons)
        conds = cast(Tuple[Sentence], conds)
        new_rule = Rule(conds, cons)
        self.add_rule(new_rule)

    def add_new_sentences(self, rule : Rule, matching : Matching):
        cons = [c.substitute(matching) for c in rule.consecuences]
        con_s = '; '.join([str(c) for c in cons])
        self.pending += cons
        self.process()

    def process(self):
        try:
            if not self.processing:
                self.processing = True
                while self.pending:
                    s = self.pending.pop()
                    if not self.ask(s):
                        logger.info(f'adding sentence "{s}"')
                        self.sset.add_sentence(s)
                        self.add_sentence(s)
        finally:
            self.processing = False

