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

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from .core import Syntagm, Sentence, Path, Matching


@dataclass
class BaseSSNode:
    '''
    Base class for sentence set nodes
    '''
    parent : Optional[BaseSSNode] = None
    children : Dict[Syntagm, 'SSNode'] = field(default_factory=dict)
    response : List[Matching] = field(default_factory=list)

    def add_paths(self, paths : List[Path], visited : List[BaseSSNode]):
        node = self
        for i, path in enumerate(paths):
            for j, segment in enumerate(path.segments):
                if segment in node.children:
                    node = node.children[segment]
                else:
                    rest_path = path.segments[j:]
                    path_rest = Path(path.value, path.var, rest_path)
                    rest_paths = [path_rest] + paths[i + 1:]
                    last_node = self.create_paths(rest_paths, visited)
                    return last_node
            visited = visited + [node]
        return node

    def create_paths(self, paths : List[Path], visited : List[BaseSSNode]):
        for path in paths:
            for node in visited:
                tovisit = []
                for segment in path.segments:
                    new_node = SSNode(value=segment,
                                      var=segment.is_var(),
                                      parent=node)
                    node.children[segment] = new_node
                    node = new_node
                tovisit.append(node)
            visited += tovisit
        return node

    def query_paths(self, paths : List[Path], matching : Matching):
        node = self
        for i, path in enumerate(paths):
            for j, segment in enumerate(path.segments):
                if segment.is_var():
                    if segment in matching:
                        segment = matching[segment]
                    else:
                        for s in node.children.values():
                            new_matching = matching.setitem(segment, s.value)
                            rest_path = path.segments[j:]
                            path_rest = Path(path.value, path.var, rest_path)
                            rest_paths = [path_rest] + paths[i + 1:]
                            self.query_paths(rest_paths, new_matching)
                if segment in node.children:
                    node = node.children[segment]
                else:
                    return
        self.response.append(matching)


@dataclass
class ContentSSNode:
    value : Syntagm
    var : bool


@dataclass
class SSNode(BaseSSNode, ContentSSNode):
    pass


@dataclass
class SentenceSet(BaseSSNode):

    def add_sentence(self, sentence: Sentence):
        paths = sentence.get_paths()
        node = self.add_paths(paths, [])

    def ask_sentence(self, sentence : Sentence) -> Optional[List[Matching]]:
        self.response = []
        paths = sentence.get_paths()
        matching = Matching()
        self.query_paths(paths, matching)
        return self.response
