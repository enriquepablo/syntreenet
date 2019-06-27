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
from typing import List, Dict, Optional

from .core import Syntagm, Sentence, Path, Matching
from .util import get_parents


@dataclass
class BaseSSNode:
    '''
    Base class for sentence set nodes
    '''
    parent : Optional[BaseSSNode] = None
    children : Dict[Path, 'SSNode'] = field(default_factory=dict)
    response : List[Matching] = field(default_factory=list)

    def follow_paths(self, paths : List[Path]):
        parent = self
        for i, path in enumerate(paths):
            node = parent.children.get(path)
            if node is None:
                parent.create_paths(paths[i:])
                return
            parent = node

    def create_paths(self, paths : List[Path]):
        visited = get_parents(self)
        if paths:
            path = paths.pop()
            for node in visited:
                if path.can_follow(node.path):
                    new_node = SSNode(path=path,
                                      var=path.var,
                                      parent=node)
                    node.children[path] = new_node
                    new_node.create_paths(copy(paths))

    def query_paths(self, paths : List[Path], matching : Matching):
        if paths:
            path = paths.pop()
            syn = path.value
            child : Optional[SSNode]
            if path.var:
                if syn in matching:
                    old_syn = matching[syn]
                    path = path.change_value(old_syn)
                    paths = [p.change_subpath(path, old_syn) for p in paths]
                else:
                    for child in self.children.values():  # type
                        new_path = path.change_value(child.path.value)
                        rest_paths = [p.change_subpath(new_path, syn) for p in paths]
                        new_matching = matching.setitem(syn, child.path.value)
                        child.query_paths(rest_paths, new_matching)
            child = self.children.get(path)
            if child is not None:
                child.query_paths(paths, matching)
        else:
            self.response_append(matching)

    def response_append(self, matching : Matching):
        if self.parent is None:
            self.response.append(matching)
        else:
            self.parent.response_append(matching)


@dataclass
class ContentSSNode:
    path : Path
    var : bool


@dataclass
class SSNode(BaseSSNode, ContentSSNode):
    pass


@dataclass
class SentenceSet(BaseSSNode):

    def add_sentence(self, sentence: Sentence):
        paths = sentence.get_paths()
        self.follow_paths(paths)

    def ask_sentence(self, sentence : Sentence) -> Optional[List[Matching]]:
        self.response = []
        paths = sentence.get_paths()
        matching = Matching()
        self.query_paths(paths, matching)
        return self.response
