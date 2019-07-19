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
from typing import List, Tuple, Optional, Any, cast

from parsimonious.nodes import Node
from parsimonious.expressions import Expression


@dataclass(frozen=True)
class Segment:
    '''
    '''
    expr : Expression
    text : str
    start : int = 0
    end : int = 0
    leaf : bool = False
    identity_tuple : tuple = field(init=False)

    def __post_init__(self):
        self.identity_tuple = (self.expr.name, self.text)
        if self.end == 0:
            self.end = len(self.text)

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f'<Segment: {self.expr.name}: {self}>'

    def __hash__(self) -> int:
        return hash(self.identity_tuple)

    def __equals__(self, other : Segment) -> bool:
        return self.identity_tuple == other.identity_tuple

    def is_var(self) -> bool:
        '''
        Whether the segment represents a variable.
        '''
        return self.expr.name == 'var'

    def can_be_var(self) -> bool:
        return self.expr.name == 'var' or self.expr.name.startswith('v_')

    def substitute(self, matching : Matching) -> Segment:
        matched = matching.get(self)
        if matched is not None:
            text = matched.text
            expr = matched.expr
            start = self.start
            end = self.start + len(matched.text)
            return Segment(text, expr, start, end, True)
        return self


def make_var(n : int) -> Segment:
    text = f'__X{n}'
    expr = Expression(name='var')
    return Segment(text, expr)


@dataclass(frozen=True)
class Path:
    '''
    '''
    segments : tuple = field(default_factory=tuple)  # Tuple[Segment...]
    identity_tuple : tuple = field(init=False)
    deep_identity_tuple : tuple = field(init=False)

    def __post_init__(self):
        self.identity_tuple = (tuple(s.expr.name for s in self.segments) +
                                (self.segments[-1].text,))
        self.deep_identity_tuple = tuple(hash(s.expr) for s in self.segments)

    def __str__(self) -> str:
        return ' -> '.join([str(s) for s in self.segments])

    def __repr__(self) -> str:
        return f'<Path: {str(self)}>'

    def __hash__(self) -> int:
        return hash(self.identity_tuple)

    def __len__(self) -> int:
        return len(self.segments)

    def __equals__(self, other : Path) -> bool:
        return self.identity_tuple == other.identity_tuple

    def __getitem__(self, key : int) -> Segment:
        return self.segments[key]

    @property
    def value(self) -> Segment:
        '''
        Return the string value (expr) of the last segment
        '''
        return self.segments[-1]

    def is_var(self) -> bool:
        '''
        Return whether the last segment is a var
        '''
        return self.segments[-1].is_var()

    def can_be_var(self) -> bool:
        v = self[-1]
        return v.is_var() or v.expr.name.startswith('v_')

    def is_leaf(self) -> bool:
        '''
        Return whether this is the path of a leaf
        '''
        return self[-1].leaf

    def starts_with(self, path : Path) -> bool:
        len_path = len(path)
        if (len(self) >= len_path and
               path.deep_identity_tuple == self.deep_identity_tuple[:len_path]):
            return True
        return False

    def paths_after(self, paths : List[Path]) -> List[Path]:
        seen = False
        new_paths = []
        for p in paths:
            if not seen and p.starts_with(self):
                seen = True
            elif seen and not p.starts_with(self):
                new_paths.append(p)
        return new_paths

    def get_subpath(self, path : Path) -> Path:
        segments = self.segments[:len(path)]
        return Path(segments)

    def substitute(self, matching : Matching) -> Tuple[Path, Optional[Path]]:
        '''
        Return a new Path copy of self where if a segment appears as key in
        matching it has been replaced by the corresponding value.
        '''
        new_segments = []
        for segment in self.segments:
            new_segment = segment.substitute(matching)
            new_segments.append(new_segment)
            if segment != new_segment:
                offset = new_segment.end - segment.end
                old_path = Path(tuple(new_segments[:-1]) + (segment,))
                break
        else:
            return self, None
        
        real_new_segments = []
        prev = new_segments[-1]
        for segment in new_segments[-2::-1]:
            text = (segment.text[:prev.start] +
                    prev.text +
                    segment.text[prev.end:])
            end = segment.end + offset
            new_segment = Segment(text, segment.expr, segment.start, end, False)
            real_new_segments.append(new_segment)
            prev = segment
        
        segments = tuple(real_new_segments[-1::-1]) + (prev,)
        return Path(segments), old_path

    @staticmethod
    def substitute_paths(paths, matching: Matching) -> List[Path]:
        '''
        '''
        new_paths = []
        old_paths : List[Path] = []
        while paths:
            path = paths.pop(0)
            for old_path in old_paths:
                if path.starts_with(old_path):
                    break
            else:
                new_path, old_path = path.substitute(matching) 
                if old_path:
                    old_paths.append(old_path)
                if new_path.is_leaf():
                    new_paths.append(new_path)
        return new_paths


@dataclass(frozen=True)
class Fact:
    '''
    '''
    text : str
    paths : tuple = field(default_factory=tuple)

    def get_all_paths(self) -> tuple:
        return copy(self.paths)

    def get_leaf_paths(self) -> tuple:
        return tuple(p for p in self.paths if p.is_leaf())

    @classmethod
    def from_parse_tree(cls, tree : Node) -> Fact:
        '''
        Build fact from a list of paths.
        '''
        segment_tuples : List[tuple] = []
        cls._visit_pnode(tree, (), segment_tuples)
        paths = tuple(Path(s) for s in segment_tuples)
        return cls(tree.text, paths)

    @classmethod
    def _visit_pnode(cls, node : Node, root_path : tuple,
            all_paths : List[tuple], parent : Node = None):
        expr = node.expr
        text = node.full_text[node.start: node.end]
        try:
            start = node.start - cast(Segment, parent).start
            end = node.end - cast(Segment, parent).start
        except AttributeError:  # node is root node
            start, end = 0, len(text)
        segment = Segment(expr, text, start, end, not bool(node.children))
        path = root_path + (segment,)
        if segment.can_be_var():
            all_paths.append(path)
        for child in node.children:
            cls._visit_pnode(child, path, all_paths, parent=node)

    def substitute(self, matching: Matching, kb) -> Fact:
        '''
        Return a new fact, copy of self, where every appearance of the
        syntagms given as keys in the matching has been replaced with the
        syntagm given as value for the key in the matching.
        '''
        new_paths = Path.substitute_paths(copy(self.paths), matching)
        strfact = ''.join([p.value.text for p in new_paths])
        tree = kb.parse(strfact)
        return self.from_parse_tree(tree)


    def normalize(self, kb : Any) -> Tuple[Matching, tuple]:
        '''
        When the condition of a rule is added to the network, the variables it
        carries are replaced by standard variables, so that all conditions deal
        with the same variables. The 1st variable in the condition will be
        called __X1, the 2nd __X2, etc.
        The method will return the paths of the normalized condition, along
        with a matching representing all the variable replacements that have
        been done.
        '''
        varmap = Matching(origin=self)
        counter = 1
        for path in self.get_leaf_paths():
            if path.is_var():
                new_var = varmap.get(path.value)
                if new_var is None:
                    new_var = make_var(counter)
                    counter += 1
                    varmap = varmap.setitem(path.value, new_var)
        new_fact = self.substitute(varmap, kb)
        return varmap.invert(), new_fact.paths


@dataclass(frozen=True)
class Matching:
    '''
    A matching is basically a mapping of Segments.
    '''
    mapping : tuple = field(default_factory=tuple)  # Tuple[Tuple[Segment, Segment]]
    origin : Optional[Fact] = None

    def __str__(self) -> str:
        return ', '.join([f'{k} : {v}' for k, v in self.mapping])

    def __repr__(self) -> str:
        return f'<Match: {str(self)}>'

    def __getitem__(self, key : Segment) -> Segment:
        for k, v in self.mapping:
            if k == key:
                return v
        raise KeyError(f'key {key} not in {self}')

    def __contains__(self, key : Segment) -> bool:
        for k, _ in self.mapping:
            if k == key:
                return True
        return False

    def copy(self) -> Matching:
        '''
        Return a copy of self
        '''
        return Matching(mapping=copy(self.mapping), origin=self.origin)

    def get(self, key : Segment) -> Optional[Segment]:
        '''
        Return the value corresponding to the provided key, or None if the key
        is not present.
        '''
        for k, v in self.mapping:
            if k == key:
                return v
        return None

    def getkey(self, value : Segment) -> Optional[Segment]:
        '''
        Return the key corresponding to the provided value, or None if the
        value is not present.
        '''
        for k, v in self.mapping:
            if value == v:
                return k
        return None

    def setitem(self, key : Segment, value : Segment) -> Matching:
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
        return Matching(mapping_tuple, self.origin)

    def merge(self, other : Matching) -> Matching:
        '''
        '''
        nextmap = dict(self.mapping)
        for k, v in other.mapping:
            if k in nextmap and v != nextmap[k]:
                raise ValueError(f'Merge error {self} and {other}')
            nextmap[k] = v
        mapping_tuple = tuple((k, v) for k, v in nextmap.items())
        return Matching(mapping_tuple, self.origin)

    def invert(self) -> Matching:
        '''
        Return a new Matching, where the keys are the values in self and the
        values the keys.
        '''
        mapping = tuple((v, k) for k, v in self.mapping)
        return Matching(mapping, self.origin)

    def get_real_matching(self, varmap : Matching) -> Matching:
        '''
        Replace the keys in self with the values in varmap corresponding to
        those keys.
        '''
        real_mapping = []
        for k, v in self.mapping:
            k = varmap.get(k) or k
            real_mapping.append((k, v))
        return Matching(tuple(real_mapping), self.origin)
