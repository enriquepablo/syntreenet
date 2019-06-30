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

from copy import deepcopy
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from .core import Syntagm, Sentence, Path, Matching
from .util import get_parents
from .logging import logger


@dataclass
class BaseSSNode:
    '''
    Base class for sentence set nodes. Nodes have a parent that is either the
    sentence set or another node, and children, which is a dictionary of paths
    to nodes.
    '''
    parent : Optional[BaseSSNode] = None
    children : Dict[Path, 'SSNode'] = field(default_factory=dict)
    response : List[Matching] = field(default_factory=list)

    def follow_paths(self, paths : List[Path]):
        '''
        Used while adding new sentences, to find the sequence of already
        existing nodes that correpond to its list of paths.
        '''
        parent = self
        for i, path in enumerate(paths):
            node = parent.children.get(path)
            if node is None:
                rest = paths[i:]
                parent.create_paths(rest)
                return
            parent = node

    def create_paths(self, paths : List[Path]):
        '''
        Used while adding new sentences, to create the sequence of
        nodes that correpond to its list of paths and did not exist previously.
        '''
        visited = get_parents(self)
        if paths:
            path = paths.pop(0)
            for node in visited:
                if hasattr(node, 'path') and not path.can_follow(node.path):
                    continue
                new_node = SSNode(path=path,
                                  var=path.var,
                                  parent=node)
                node.children[path] = new_node
                new_node.create_paths(deepcopy(paths))

    def query_paths(self, paths : List[Path], matching : Matching):
        '''
        Match the paths corresponding to a query (possibly containing
        variables) with the paths in the nodes of the sentence set.
        '''
        if paths:
            path = paths.pop(0)
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
            self._response_append(matching)

    def _response_append(self, matching : Matching):
        logger.debug(f'answer with {matching.mapping}')
        if self.parent is None:
            self.response.append(matching)
        else:
            self.parent._response_append(matching)


@dataclass
class ContentSSNode:
    '''
    A node with content, i.e., that corresponds to a syntactic element whithin a
    sentence.
    '''
    path : Path
    var : bool


@dataclass
class SSNode(BaseSSNode, ContentSSNode):
    '''
    Concrete nodes in the sentence set.
    '''

    def __str__(self):
        return f'node : {self.path}'


@dataclass
class SentenceSet(BaseSSNode):
    '''
    A set of sentences arranged in a tree structure that facilitates queries.
    '''

    def __str__(self):
        return 'sset'

    def add_sentence(self, sentence: Sentence):
        '''
        Add a new sentence to the set.
        '''
        logger.debug(f'adding sentence {sentence} to sset')
        paths = sentence.get_paths()
        self.follow_paths(paths)

    def ask_sentence(self, sentence : Sentence) -> List[Matching]:
        '''
        Query a sentence, possibly with variables. If the query matches no
        sentences, the return value will be False. If the query matches
        sentences, the return value will consist on all the assignments of the
        variables in the query that correspond to a sentence in the set - or
        True if there are no variables.
        '''
        self.response = []
        paths = sentence.get_paths()
        matching = Matching()
        self.query_paths(paths, matching)
        if not self.response:
            return False
        if len(self.response) == 1 and not self.response[0].mapping:
            return True
        return self.response
