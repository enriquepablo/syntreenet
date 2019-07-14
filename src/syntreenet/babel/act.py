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

from dataclasses import field, dataclass
from collections import OrderedDict
from typing import List

from ..core import Syntagm, Fact, Path
from ..ruleset import Rule, KnowledgeBase



class PathOrder:

    @staticmethod
    def can_follow(snd : Path, fst : Path) -> bool:
        return True

    @staticmethod
    def can_be_first(path : Path) -> bool:
        return False

    @classmethod
    def new_var(cls, seed):
        return Word(f'__X{seed}', True)


@dataclass(frozen=True, order=True)
class Word(Syntagm, PathOrder):
    '''
    The syntagms in this grammar are words, with no internal structure - just a
    name.
    '''
    name : str
    var : bool = False
    extra_var : bool = False

    def __str__(self):
        return self.name

    def is_var(self):
        return self.var

    def is_extra_var(self):
        return self.extra_var

    def to_odict(self):
        return self

    @classmethod
    def from_odict(cls, syn):
        return syn

nothing = Word('__nothing')
empty_path = Path(nothing)

@dataclass(frozen=True, order=True)
class Expression(Syntagm, PathOrder):
    '''
    '''
    pairs : tuple = field(default_factory=tuple)
    extra_var : Optional[Syntagm] = None

    def __str__(self):
        return '(%s)' % ', '.join([f'{k}: {v}' for k, v in self.pairs])

    def __getitem__(self, key):
        for k, v in self.pairs:
            if k == key:
                return v
        raise KeyError(f'{self} has no key {key}')

    def is_var(self):
        return False

    def is_extra_var(self):
        return False

    @classmethod
    def from_odict(cls, odict, extra_var=None):
        pairs = []
        for k, v in odict.items():
            pairs.append((k, v.from_odict(v)))
        return cls(pairs, extra_var)

    def to_odict(self):
        odict = OrderedDict()
        for k, v in self.pairs:
            odict[k] = v.to_odict()
        return odict

    def get_path_list(self, base : tuple) -> List[Path]:
        path_list = []
        for k, v in self.pairs:
            new_base = base + (k,)
            if isinstance(v.extra_var, Syntagm):
                path_list.append(Path.from_segments(new_base + (v.extra_var,)))
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

    def match_path(self, path):
        expr = self.expr
        for s in path.segments[:-1]:
            expr = expr[s]
        return path[-1], expr

    @classmethod
    def from_paths(cls, paths):
        odict = OrderedDict()
        extra_vars = []
        for path in paths:
            if path[-1].is_extra_var():
                extra_vars.append(path)
            else:
                self._add_path_to_odict(path)

        f = cls(Expression.from_odict(odict))
        for ev in extra_vars:
            f.add_extra_var(ev)
        return f

    def add_extra_var(self, var):
        root = parent = self.expr.to_odict()
        expr = None
        for s in path.segments[:-1]:
            parent = expr
            expr = parent[s]
        new_expr = Expression(expr.pairs, var)
        parent[s] = new_expr
        return F(Expression.from_odict(root))

    def _add_path_to_odict(self, segments, odict):
        key = segments[0]
        if len(segments) == 2:
            odict[key] = segments[1]
        else:
            if key in odict:
                subodict = odict[key]
            else:
                subodict = OrderedDict()

            odict[key] = self._add_path_to_odict(segments[1:], subodict)
        return odict


X1 = Word('X1', var=True)
X2 = Word('X2', var=True)
X3 = Word('X3', var=True)

time = Word('time')
verb = Word('verb')
should = Word('should')
can = Word('can')
what = Word('what')

prem1 = F((((verb, can), (can, X1)


'''
(verb: can, can: X1, what: [X2](verb: X3, X3: X1))
(verb: should, should: X1, what: [X4](X2))
->
(X4)
 = Word('')
 = Word('')
 = Word('')
 = Word('')








X1 can 

placed

at

move

from, towards

body1

place1, place2

X1 should move from X2 to X3
X1 placed at X2
->
X1 can move from X2 to X3

(verb: should, should: body1, what: (verb: move



------------------------

will - goals

knowledge - timeless factset and ruleset

present - timeful factset and ruleset

query present and knowledge with goals

add the facts needed to fulfill the goals

interchange present with peers

put info from peers in next present

advance time and add past present to present with the consecuences of passing
time

query new present with goals...


'''



'''
When matchng facts in rule sets, 


get_paths must return paths in the same way query uses the queried paths or
create paths used the parents adding rules.

it must return expressions as values in paths, in as many subdivisions as makes
sense. 

perhaps we need 2 get_paths, one to build the rules limited to provide the
paths present in the rule, 


No - what we need are special variables, for which value we need to query the
matching facts, and are simply stored until used in consecuences. When they are
repeated in another condition, mmmmm.... we produce a new rule, so we must use
the matching that we have.

I see it like theexpr will ony be used in a condition of the new rule if it
wont overwrite any other expr. so its substitution must be delayed untl all
normal substitutions have taken place.
'''
