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
from typing import List, Dict, Optional, Any, cast

from .grammar import Fact, Path, Matching


@dataclass
class BaseSSNode:
    '''
    Base class for fact set nodes. Nodes have a parent that is either the
    fact set or another node, and children, which is a dictionary of paths
    to nodes.
    '''
    parent : Optional[BaseSSNode]
    logic_children : Dict[Path, 'SSNode'] = field(default_factory=dict)
    nonlogic_children : Dict[Path, 'SSNode'] = field(default_factory=dict)

    def get_fact_leaf(self, paths : List[Path]) -> Optional[SSNode]:
        parent = self
        for i, path in enumerate(paths):
            node = parent.nonlogic_children.get(path)
            if node is None:
                node = parent.logic_children.get(path)
            if node is None:
                return None
            parent = node
        return cast(SSNode, parent)

    def follow_paths(self, paths : List[Path], kb : Any):
        '''
        Used while adding new facts, to find the sequence of already
        existing nodes that correpond to its list of paths.
        '''
        parent = self
        for i, path in enumerate(paths):
            if kb.in_var_range(path):
                node = parent.logic_children.get(path)
                if not path.is_leaf():
                    new_paths = path.paths_after(paths)
                    if node:
                        node.follow_paths(new_paths, kb)
                    else:
                        parent._create_paths([path] + new_paths, kb)
                    continue
            else:
                node = parent.nonlogic_children.get(path)
            if node is None:
                parent._create_paths(paths[i:], kb)
                return
            parent = node

    def _create_paths(self, paths : List[Path], kb : Any):
        '''
        Used while adding new facts, to create the sequence of
        nodes that correpond to its list of paths and did not exist previously.
        '''
        parent = self
        for path in paths:
            new_node = SSNode(path=path,
                              var=path.is_var(),
                              parent=parent)
            if kb.in_var_range(path):
                parent.logic_children[path] = new_node
                if not path.is_leaf():
                    new_paths = path.paths_after(paths)
                    new_node._create_paths(new_paths, kb)
                    continue
            else:
                parent.nonlogic_children[path] = new_node
            parent = new_node

    def query_paths(self, paths : List[Path], matching : Matching, kb : Any):
        '''
        Match the paths corresponding to a query (possibly containing
        variables) with the paths in the nodes of the fact set.
        '''
        if paths:
            path = paths.pop(0)
            syn = path.value
            child : Optional[SSNode]
            if path.is_var():
                if syn not in matching:
                    for child in self.logic_children.values():
                        new_matching = matching.setitem(syn, child.path.value)
                        child.query_paths(copy(paths), new_matching, kb)
                    return
                else:
                    path, _ = path.substitute(matching)

            if kb.in_var_range(path):
                next_node = self.logic_children.get(path)
            else:
                next_node = self.nonlogic_children.get(path)
            if next_node:
                next_node.query_paths(paths, matching, kb)

        else:
            self._response_append(matching)

    def _response_append(self, matching : Matching):
        if self.parent is None:
            cast(FactSet, self).response.append(matching)
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
    parent : BaseSSNode


@dataclass
class FactSet(BaseSSNode):
    '''
    A set of facts arranged in a tree structure that facilitates queries.
    '''
    parent : Optional[BaseSSNode] = None
    kb : Any = None
    response : List[Matching] = field(default_factory=list)

    def add_fact(self, fact: Fact):
        '''
        Add a new fact to the set.
        '''
        paths = fact.get_all_paths()
        self.follow_paths(paths, self.kb)

    def ask_fact(self, fact : Fact) -> List[Matching]:
        '''
        '''
        self.response = []
        paths = fact.get_leaf_paths()
        matching = Matching(origin=fact)
        self.query_paths(paths, matching, self.kb)
        return self.response

    def rm_fact(self, fact : Fact, kb : Any):
        '''
        '''
        paths = fact.get_leaf_paths()
        leaf = self.get_fact_leaf(paths)
        while (leaf and
                not leaf.logic_children and
                not leaf.nonlogic_children and
                leaf is not self):
            parent = leaf.parent
            path = leaf.path
            if kb.in_var_range(path):
                del parent.logic_children[path]
            else:
                del parent.nonlogic_children[path]
            leaf = cast(SSNode, parent)
