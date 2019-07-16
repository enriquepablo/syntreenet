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
from abc import ABC
from typing import List, Tuple, Optional


@dataclass(frozen=True)
class Segment(ABC):
    '''
    '''
    expr : str
    text : str
    start : int
    end : int

    def is_var(self) -> bool:
        '''
        Whether the segment represents a variable.
        '''

    def is_extra_var(self) -> bool:
        '''
        Whether the segment represents an extra variable.
        '''
        # XXX if shorter sfacts being impied by longer facts belongs to the
        # logics, thwn this is just  a shortcut and worthless XXX


@dataclass(frozen=True)
class Path:
    '''
    '''
    segments : tuple = field(default_factory=tuple)  # Tuple[Segment...]
    var : bool = False

    def __str__(self):
        return ' -> '.join([str(s) for s in self.segments])

    def __repr__(self):
        return f'<Path: {str(self)}>'

    @property
    def value(self):
        '''
        Return the last segment
        '''
        return self.segments[-1]

    @property
    def var(self):
        '''
        Return whether the last segment is a var
        '''
        return self.segments[-1].is_var()

    def extra_var(self) -> bool:
        return self.segments[-1].is_extra_var()

    def substitute(self, varmap : Matching) -> Path:
        '''
        Return a new Path copy of self where the syntagms appearing as keys in
        varmap have been replaced by their corresponding values.
        '''
        # XXX when a segment is changed, the text of the rest of the segments in
        # the path must also change XXX
        segments = tuple([s in varmap and varmap[s] or s for s in
            self.segments])
        if segments == self.segments:
            return self
        return Path(segments)

    def change_value(self, val : Syntagm) -> Path:
        '''
        Return new Path, copy of self, where the value -the last syntagm in the
        tuple- has been changed for the one provided in val.
        '''
        # XXX when a segment is changed, the text of the rest of the segments in
        # the path must also change XXX
        return Path(self.segments[:-1] + (val,))

    def can_follow(self, base : Path) -> bool:
        '''
        Can the syntactic element represented by self occur immediately to the
        right of the one represented by base?
        '''
        raise NotImplementedError('''XXX  XXX XXX forEVER THIS IS A WRONG IDEA
        THIS BELONGS IN THE LOGICS FOR GOS'S SAKE''')

    def can_be_first(self) -> bool:
        '''
        Can the syntactic element represented by self occur as the first
        element in a fact?
        '''
        raise NotImplementedError('''XXX  XXX XXX forEVER THIS IS A WRONG IDEA
        THIS BELONGS IN THE LOGICS FOR GOS'S SAKE''')

    def change_subpath(self, path : Path, old_value : Syntagm) -> Path:
        '''
        If the provided path (with old_value as value) is a subpath of self,
        replace that subpath with the provided path and its current value, and
        return it as a new path.
        '''
        if len(self.segments) < len(path.segments):
            return self
        new_segments = []
        for base, this in zip(path.segments[:-1], self.segments):
            if base == this:
                new_segments.append(base)
            else:
                break
        else:
            l = len(new_segments)
            if self.segments[l] == old_value:
                new_segments.append(path.segments[l])
                new_segments += self.segments[l + 1:]
                new_value = new_segments[-1]
                return Path(new_value, new_value.is_var(), tuple(new_segments))
        return self

from parsimonious.nodes import Node

@dataclass(frozen=True)
class Fact(ABC):
    '''
    '''
    text : str
    paths : Tuple[Path] = field(default_factory=list)

    @classmethod
    def from_parse_tree(cls, tree : Node) -> Fact:
        '''
        Build fact from a list of paths.
        '''
        segment_list = []
        cls._visit_pnode(tree, (), segment_list)
        return Path(tree.text, tuple(segment_list))

    @classmethod
    def _visit_pnode(cls, node, root_path, all_paths, parent=None):
        expr = node.expr
        text = node.full_text[node.start: node.end]
        if parent:
            start = node.start - parent.start
            end = node.end - parent.start
        else:
            start, end = 0, len(text)
        segment = Segment(expr, text, start, end)
        path = root_path + (segment,)
        all_paths.append(path)
        for child in node.children:
            cls._visit_pnode(child, path, all_paths)

    def match_path(self, path : Path) -> Tuple[Syntagm, Syntagm]:
        '''
        Get the syntagm that corresponds to self.segments[:-1] and return it
        matched to self.segments[1]
        '''
        raise NotImplementedError()

    def substitute(self, matching: Matching) -> Fact:
        '''
        Return a new fact, copy of self, where every appearance of the
        syntagms given as keys in the matching has been replaced with the
        syntagm given as value for the key in the matching.
        '''
        paths = self.get_paths()
        new_paths = []
        for path in paths:
            new_path = path.substitute(matching)
            new_paths.append(new_path)
        return self.from_paths(new_paths)

    def normalize(self) -> Tuple[Matching, List[Path]]:
        '''
        When the condition of a rule is added to the network, the variables it
        carries are replaced by standard variables, so that all conditions deal
        with the same variables. The 1st variable in the condition will be
        called __X1, the 2nd __X2, etc.
        The method will return the paths of the normalized condition, along
        with a matching representing all the variable replacements that have
        been done.
        '''
        paths = self.get_paths()
        new_paths = []
        varmap = Matching(origin=self)
        counter = 1
        for path in paths:
            if path.var:
                new_var = varmap.get(path.value)
                if new_var is None:
                    new_var = path.value.new_var(counter)
                    counter += 1
                    varmap = varmap.setitem(path.value, new_var)
            new_path = path.substitute(varmap)
            new_paths.append(new_path)
        return varmap.invert(), new_paths


@dataclass(frozen=True)
class Matching:
    '''
    A matching is basically a mapping of Syntagms.
    '''
    mapping : tuple = field(default_factory=tuple)  # Tuple[Tuple[Syntagm, Syntagm]]
    origin : Optional[Fact] = None

    def __str__(self):
        return ', '.join([f'{k} : {v}' for k, v in self.mapping])

    def __repr__(self):
        return f'<Match: {str(self)}>'

    def __getitem__(self, key : Syntagm) -> Syntagm:
        for k, v in self.mapping:
            if k == key:
                return v
        raise KeyError(f'key {key} not in {self}')

    def __contains__(self, key : Syntagm) -> bool:
        for k, _ in self.mapping:
            if k == key:
                return True
        return False

    def copy(self) -> Matching:
        '''
        Return a copy of self
        '''
        return Matching(mapping=copy(self.mapping), origin=self.origin)

    def get(self, key : Syntagm) -> Optional[Syntagm]:
        '''
        Return the value corresponding to the provided key, or None if the key
        is not present.
        '''
        try:
            return self[key]
        except KeyError:
            return None

    def getkey(self, value : Syntagm) -> Optional[Syntagm]:
        '''
        Return the key corresponding to the provided value, or None if the
        value is not present.
        '''
        for k, v in self.mapping:
            if value == v:
                return k
        return None

    def setitem(self, key : Syntagm, value : Syntagm) -> Matching:
        '''
        Return a new Matching, copy of self, with the addition (or the
        replacement if the key was already in self) of the new key value pair.
        '''
        spent = False
        mapping = []
        for k, v in self.mapping:
            if k == key:
                mapping.append((key, value))
                spent = True
            else:
                mapping.append((k, v))
        if not spent:
            mapping.append((key, value))
        mapping_tuple = tuple(mapping)
        return Matching(mapping_tuple)

    def merge(self, other : Matching) -> Matching:
        '''
        '''
        nextmap = dict(self.mapping)
        for k, v in other.mapping:
            if k in nextmap and v != nextmap[k]:
                raise ValueError(f'Merge error {self} and {other}')
            nextmap[k] = v
        mapping_tuple = tuple((k, v) for k, v in nextmap.items())
        return Matching(mapping=mapping_tuple, origin=self.origin)

    def invert(self) -> Matching:
        '''
        Return a new Matching, where the keys are the values in self and the
        values the keys.
        '''
        mapping = tuple((v, k) for k, v in self.mapping)
        return Matching(mapping=mapping, origin=self.origin)

    def get_real_matching(self, varmap : Matching) -> Matching:
        '''
        Replace the keys in self with the values in varmap corresponding to
        those keys.
        '''
        real_mapping = []
        for k, v in self.mapping:
            k = varmap.get(k) or k
            real_mapping.append((k, v))
        return Matching(mapping=tuple(real_mapping), origin=self.origin)


def 
