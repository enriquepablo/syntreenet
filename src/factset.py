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

from .core import Syntagm, Fact, Path, Matching
from .util import get_parents
from .logging import logger


@dataclass
class BaseSSNode:
    '''
    Base class for fact set nodes. Nodes have a parent that is either the
    fact set or another node, and children, which is a dictionary of paths
    to nodes.
    '''
    parent : Optional[BaseSSNode] = None
    children : Dict[Path, 'SSNode'] = field(default_factory=dict)
    response : List[Matching] = field(default_factory=list)

    def follow_paths(self, paths : List[Path]):
        '''
        Used while adding new facts, to find the sequence of already
        existing nodes that correpond to its list of paths.
        '''
        parent = self
        for i, path in enumerate(paths):
            node = parent.children.get(path)
            if node is None:
                rest = paths[i:]
                first = isinstance(self, FactSet)
                parent.create_paths(rest, first=first)
                return
            parent = node

    def create_paths(self, paths : List[Path], first : bool = False):
        '''
        Used while adding new facts, to create the sequence of
        nodes that correpond to its list of paths and did not exist previously.
        '''
        visited = get_parents(self)
        if paths:
            path = paths.pop(0)
            for node in visited:
                if hasattr(node, 'path'):
                    if not path.can_follow(node.path):
                        continue
                elif not first:
                    continue
                new_node = SSNode(path=path,
                                  var=path.var,
                                  parent=node)
                node.children[path] = new_node
                new_node.create_paths(copy(paths))

    def query_paths(self, paths : List[Path], matching : Matching):
        '''
        Match the paths corresponding to a query (possibly containing
        variables) with the paths in the nodes of the fact set.
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
    fact.
    '''
    path : Path
    var : bool


@dataclass
class SSNode(BaseSSNode, ContentSSNode):
    '''
    Concrete nodes in the fact set.
    '''

    def __str__(self):
        return f'node : {self.path}'


@dataclass
class FactSet(BaseSSNode):
    '''
    A set of facts arranged in a tree structure that facilitates queries.
    '''

    def __str__(self):
        return 'fset'

    def add_fact(self, fact: Fact):
        '''
        Add a new fact to the set.
        '''
        logger.debug(f'adding fact {fact} to fset')
        paths = fact.get_paths()
        self.follow_paths(paths)

    def ask_fact(self, fact : Fact) -> List[Matching]:
        '''
        Query a fact, possibly with variables. If the query matches no
        facts, the return value will be False. If the query matches
        facts, the return value will consist on all the assignments of the
        variables in the query that correspond to a fact in the set - or
        True if there are no variables.
        '''
        self.response = []
        paths = fact.get_paths()
        matching = Matching()
        self.query_paths(paths, matching)
        if not self.response:
            return False
        if len(self.response) == 1 and not self.response[0].mapping:
            return True
        return self.response
