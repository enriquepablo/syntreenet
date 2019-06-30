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

from dataclasses import dataclass
from enum import Enum

from ..core import Syntagm, Sentence, Path
from ..ruleset import Rule, RuleSet


@dataclass(frozen=True, order=True)
class Word(Syntagm):
    name : str
    var : bool = False

    def __str__(self):
        return self.name

    def is_var(self):
        return self.var

    @classmethod
    def new_var(cls, seed):
        return Word(f'__X{seed}', True)

    def can_follow(self, snd : Path, fst : Path) -> bool:
        if fst.segments[0] == _subj and snd.segments[0] == _pred:
            return True
        if fst.segments[0] == _pred and snd.segments[0] == _obj:
            return True
        return False


_pred = Word('__pred')
_subj = Word('__subj')
_obj = Word('__obj')

@dataclass(frozen=True)
class Pred(Word):
    pass

is_ = Pred('is')
isa = Pred('isa')


@dataclass(frozen=True)
class Sen(Sentence):
    subj : Word
    pred : Pred
    obj : Word

    def __str__(self):
        return f'{self.subj} {self.pred} {self.obj}'

    def __repr__(self):
        return f'<Sen: {str(self)}>'

    def get_paths(self):
        pred_path = Path(self.pred, False, (_pred, self.pred))
        subj_path = Path(self.subj, self.subj.is_var(), (_subj, self.subj))
        obj_path = Path(self.obj, self.obj.is_var(), (_obj, self.obj))
        return [subj_path, pred_path, obj_path]

    @classmethod
    def from_paths(cls, paths):
        pred = subj = obj = None
        for path in paths:
            if path.segments[0] == _subj:
                subj = path.value
            elif path.segments[0] == _pred:
                pred = path.value
            elif path.segments[0] == _obj:
                obj = path.value
        return cls(subj, pred, obj)


X1 = Word('X1', True)
X2 = Word('X2', True)
X3 = Word('X3', True)


prem1 = Sen(X1, isa, X2)
prem2 = Sen(X2, is_, X3)
cons1 = Sen(X1, isa, X3)

rule1 = Rule((prem1, prem2), (cons1,))


prem3 = Sen(X1, is_, X2)
cons2 = Sen(X1, is_, X3)

rule2 = Rule((prem3, prem2), (cons2,))


r = RuleSet()

r.tell(rule1)
r.tell(rule2)


thing = Word('thing')
animal = Word('animal')
mammal = Word('mammal')
primate = Word('primate')
human = Word('human')
susan = Word('susan')

r.tell(Sen(animal, is_, thing))
r.tell(Sen(mammal, is_, animal))
r.tell(Sen(primate, is_, mammal))
r.tell(Sen(human, is_, primate))

r.tell(Sen(susan, isa, human))


