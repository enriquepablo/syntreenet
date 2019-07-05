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
class Syntagm(ABC):
    '''
    The components of facts. They are immutable objects with any
    domain-specific internal structure.
    They must be able to tell whether they are a variable or not, through their
    is_var method.
    '''

    @classmethod
    def new_var(cls, seed : Optional[int] = None) -> Syntagm:
        '''
        Return a syntagm that is a var,
        using the seed somehow in its internal structure.
        '''

    def is_var(self) -> bool:
        '''
        Whether the syntagm is a variable.
        '''

    @staticmethod
    def can_follow(snd : Path, fst : Path) -> bool:
        '''
        whether the 2 paths can represent contiguous syntactic elements in a
        fact, with fst to the left of snd.
        '''
        return True

    @staticmethod
    def can_be_first(path : Path) -> bool:
        '''
        whether the 2 paths can represent contiguous syntactic elements in a
        fact, with fst to the left of snd.
        '''
        return True


@dataclass(frozen=True)
class Fact(ABC):
    '''
    A fact is any syntactic construction that can be represented as a tree
    of syntagms, where the leaves are the components of the fact (there can
    be syntagms in the tree that are syntactic markers and do not participate
    in the fact).
    There is a main method that implementations of Fact must provide, which
    is get_paths. A path corresponds to a syntactic element of a fact, i.e.
    to a leaf in the fact tree, and it is formed by the sequence of
    syntagms that lead from the root to the leaf.

    So paths correspond to usages of syntagms within a fact, and are
    hashable, so we can use them as indexes for the syntactic components that
    they correspond to, and at the same time have a modifiable internal
    structure, where we can play with the variables in the rules.

    A fact corresponds uniquely to a set of paths, though there may be sets of
    paths that do not correspond t a fact.
    '''

    @classmethod
    def from_paths(cls, paths : List[Path]) -> Fact:
        '''
        Build fact from a list of paths.
        '''
        raise NotImplementedError()

    def get_paths(self) -> List[Path]:
        '''
        Get the list of paths corresponding to fact. The paths should be
        ordered in such a way that paths corresponding to elements to the left
        of other elements should come before the paths of the other elements.
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
        varmap = Matching()
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


class PathCannotBeEmpty(Exception): pass


@dataclass(frozen=True)
class Path:
    '''
    A Path is basically a tuple of Syntagms, that represent a syntagm in a
    fact.
    It has shortcuts for its value in the fact, i.e. for the last syntagm
    in the tuple.
    '''
    value : Syntagm
    var : bool = False
    segments : tuple = field(default_factory=tuple)  # Tuple[Syntagm]

    def __str__(self):
        return ' -> '.join([str(s) for s in self.segments])

    def __repr__(self):
        return f'<Path: {str(self)}>'

    def substitute(self, varmap : Matching) -> Path:
        '''
        Return a new Path copy of self where the syntagms appearing as keys in
        varmap have been replaced by their corresponding values.
        '''
        segments = tuple([s in varmap and varmap[s] or s for s in
            self.segments])
        value = self.value in varmap and varmap[self.value] or self.value
        return Path(value, value.is_var(), segments)

    def change_value(self, val : Syntagm) -> Path:
        '''
        Return new Path, copy of self, where the value -the last syntagm in the
        tuple- has been changed for the one provided in val.
        '''
        return Path(val, val.is_var(), self.segments[:-1] + (val,))

    def can_follow(self, base : Path) -> bool:
        '''
        Can the syntactic element represented by self occur immediatelly to the
        right of the one represented by base?
        '''
        try:
            return self.segments[0].can_follow(self, base)
        except KeyError:
            # a rather strange place to impose the constraint that paths cannot
            # be empty.
            raise PathCannotBeEmpty()

    def can_be_first(self) -> bool:
        '''
        Can the syntactic element represented by self occur as the first
        element in a fact?
        '''
        try:
            return self.segments[0].can_be_first(self)
        except KeyError:
            # a rather strange place to impose the constraint that paths cannot
            # be empty. But I don't have __init__ and this is the handiest
            # alternative :)
            raise PathCannotBeEmpty()

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


@dataclass(frozen=True)
class Matching:
    '''
    A matching is basically a mapping of Syntagms.
    '''
    mapping : tuple = field(default_factory=tuple)  # Tuple[Tuple[Syntagm, Syntagm]]

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
        return Matching(copy(self.mapping))

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

    def invert(self) -> Matching:
        '''
        Return a new Matching, where the keys are the values in self and the
        values the keys.
        '''
        mapping = tuple((v, k) for k, v in self.mapping)
        return Matching(mapping)

    def get_real_matching(self, varmap : Matching) -> Matching:
        '''
        Replace the keys in self with the values in varmap corresponding to
        those keys.
        '''
        real_mapping = []
        for k, v in self.mapping:
            k = varmap.get(k) or k
            real_mapping.append((k, v))
        return Matching(tuple(real_mapping))
