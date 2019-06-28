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
from abc import ABC
from typing import List, Tuple, Optional


@dataclass(frozen=True)
class Syntagm(ABC):
    '''
    the components of sentences
    '''

    @classmethod
    def new_var(cls, seed : Optional[int] = None) -> Syntagm:
        '''
        return a syntagm that is a var,
        using the seed somehow in its internal structure
        '''

    def is_var(self) -> bool:
        '''
        whether the syntagm is a var,
        '''

    def can_follow(self, snd : Path, fst : Path) -> bool:
        '''
        whether the snd path can follow the fst in a sentenceset
        '''


@dataclass(frozen=True)
class Sentence(ABC):  # ignore type

    @classmethod
    def from_paths(cls, paths : List[Path]) -> Sentence:
        '''
        build sentence from list of paths
        '''
        raise NotImplementedError()

    def get_paths(self) -> List[Path]:
        '''
        get list of paths corresponding to sentence
        '''
        raise NotImplementedError()

    def substitute(self, matching: Matching) -> Sentence:
        paths = self.get_paths()
        new_paths = []
        for path in paths:
            new_path = path.substitute(matching)
            new_paths.append(new_path)
        return self.from_paths(new_paths)

    def normalize(self) -> Tuple[Sentence, Matching, List[Path]]:
        paths = self.get_paths()
        new_paths = []
        varmap = Matching()
        counter = 1
        for path in paths:
            if path.var:
                new_var = Syntagm.new_var(counter)
                counter += 1
                varmap = varmap.setitem(new_var, path.value)
            new_path = path.substitute(varmap)
            new_paths.append(new_path)
        new = self.from_paths(new_paths)
        return new, varmap, new_paths

    def denormalize(self, varmap: Matching) -> Sentence:
        paths = self.get_paths()
        new_paths = []
        for path in paths:
            new_path = path.substitute(varmap)
            new_paths.append(new_path)
        new = self.from_paths(new_paths)
        return new


@dataclass(frozen=True)
class Path:
    value : Syntagm
    var : bool = False
    segments : tuple = field(default_factory=tuple)  # Tuple[Syntagm]

    def substitute(self, varmap : Matching) -> Path:
        segments = tuple([s in varmap and varmap[s] or s for s in
            self.segments])
        value = self.value in varmap and varmap[self.value] or self.value
        return Path(value, value.is_var(), segments)

    def change_value(self, val : Syntagm) -> Path:
        return Path(val, val.is_var(), self.segments[:-1] + (val,))

    def can_follow(self, base : Path) -> bool:
        if len(self.segments) == 0:
            return True  # ???
        return self.segments[0].can_follow(self, base)

    def change_subpath(self, path : Path, old_value : Syntagm) -> Path:
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
    mapping : tuple = field(default_factory=tuple)  # Tuple[Tuple[Syntagm, Syntagm]]

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
        return Matching(copy(self.mapping))

    def get(self, key : Syntagm) -> Optional[Syntagm]:
        try:
            return self[key]
        except KeyError:
            return None

    def getkey(self, value : Syntagm) -> Optional[Syntagm]:
        for k, v in self.mapping:
            if value == v:
                return k
        return None

    def setitem(self, key : Syntagm, value : Syntagm) -> Matching:
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
        mapping = tuple((v, k) for k, v in self.mapping)
        return Matching(mapping)

    def get_real_matching(self, varmap : Matching) -> Matching:
        mapping = tuple((varmap[k], v) for k, v in self.mapping)
        return Matching(mapping)
