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

from dataclasses import dataclass
from collections import OrderedDict

from ..core import Syntagm, Fact, Path
from ..ruleset import Rule, KnowledgeBase



class PathOrder:

    @staticmethod
    def can_follow(snd : Path, fst : Path) -> bool:
        pass

    @staticmethod
    def can_be_first(path : Path) -> bool:
        pass

    @classmethod
    def new_var(cls, seed):
        return Word(f'__X{seed}', True)


@dataclass(frozen=True, order=True)
class Word(Syntagm):
    '''
    The syntagms in this grammar are words, with no internal structure - just a
    name.
    '''
    name : str
    var : bool = False

    def __str__(self):
        return self.name

    def is_var(self):
        return self.var

    def to_odict(self):
        return self

    @classmethod
    def from_odict(cls, syn):
        return syn

nothing = Word('__nothing')
empty_path = Path(nothing)

@dataclass(frozen=True, order=True)
class Expression(Syntagm):
    '''
    '''
    pairs : tuple = field(default_factory=tuple)

    def __str__(self):
        return '(%s)' % ', '.join([f'{k}: {v}' for k, v in self.pairs])

    def is_var(self):
        return False

    @classmethod
    def from_odict(cls, odict):
        pairs = []
        for k, v in odict.items():
            pairs.append((k, v.from_odict(v)))
        return cls(pairs)

    def to_odict(self):
        odict = OrderedDict()
        for k, v in self.pairs:
            odict[k] = v.to_odict()
        return odict

    def get_path_list(self, base : tuple) -> List[Path]:
        path_list = []
        for k, v in self.pairs:
            new_base = base + (k,)
            if isinstance(v, Word):
                path_list.append(Path.from_segments(new_base + (v,)))
            else:
                path_list.extend(v.get_path_list(new_base))
        return path_list


@dataclass(frozen=True)
class F(Fact):
    '''
    '''
    expr : Expression

    def __str__(self):
        return f'{self.expr}'

    def __repr__(self):
        return f'<F: {str(self)}>'

    def get_paths(self):
        return self.expr.get_path_list(())
         

    @classmethod
    def from_paths(cls, paths):
        odict = OrderedDict()
        for path in paths:
            self._add_path_to_odict(path)

        return cls(Expression.from_odict(odict))

    def _add_path_to_odict(self, segments, odict):
        key = segments[0]
        if len(segments) == 2:
            odict[key] = segments[1]
        else:
            if key in odict:
                subodict = odict[key]
            else:
                subodict = OrderedDict()

            odict[key] = self.add_path(segments[1:], subodict)
        return odict
