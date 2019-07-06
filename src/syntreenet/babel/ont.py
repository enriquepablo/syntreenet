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

from ..core import Syntagm, Fact, Path
from ..ruleset import Rule, KnowledgeBase


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

    @classmethod
    def new_var(cls, seed):
        return Word(f'__X{seed}', True)

    @staticmethod
    def can_follow(snd : Path, fst : Path) -> bool:
        if fst.segments[0] == _subj and snd.segments[0] == _pred:
            return True
        if fst.segments[0] == _pred and snd.segments[0] == _obj:
            return True
        return False

    @staticmethod
    def can_be_first(path : Path) -> bool:
        if path.segments[0] == _subj:
            return True
        return False


# Here we define 3 special words, with purely syntactic (operational) meaning;
# we only use them to construct the paths that correspond to the facts of this
# grammar, but we do not use them in the actual facts.

_pred = Word('__pred')
_subj = Word('__subj')
_obj = Word('__obj')

@dataclass(frozen=True)
class Pred(Word):
    '''
    preds (from predicates) are just words, specially designated because they
    cannot be a variable.
    '''
    def is_var(self):
        return False

# We have just 2 preds, which we predefine, since we not ony want to offer a
# grammar but also the logic that gives form to its meaning, and we need the
# predicates in the rules that provide the logic.

is_ = Pred('is')
isa = Pred('isa')


@dataclass(frozen=True)
class F(Fact):
    '''
    A fact in this grammar has a fixed form, with 3 ordered elements: any
    non-pred word can serve as subject, any pred word can serve as
    predicate, and again any non-pred word can serve as object.
    '''
    subj : Word
    pred : Pred
    obj : Word

    def __str__(self):
        return f'{self.subj} {self.pred} {self.obj}'

    def __repr__(self):
        return f'<F: {str(self)}>'

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

# We now impose a logic on this grammar, using syntreenet


kb = KnowledgeBase()

X1 = Word('X1', var=True)
X2 = Word('X2', var=True)
X3 = Word('X3', var=True)


prem1 = F(X1, isa, X2)
prem2 = F(X2, is_, X3)
cons1 = F(X1, isa, X3)

rule1 = Rule((prem1, prem2), (cons1,))


prem3 = F(X1, is_, X2)
cons2 = F(X1, is_, X3)

rule2 = Rule((prem3, prem2), (cons2,))

kb.tell(rule1)
kb.tell(rule2)

# And we end up with an example of using the module:

thing = Word('thing')
animal = Word('animal')
mammal = Word('mammal')
primate = Word('primate')
human = Word('human')
susan = Word('susan')

kb.tell(F(animal, is_, thing))
kb.tell(F(mammal, is_, animal))
kb.tell(F(primate, is_, mammal))
kb.tell(F(human, is_, primate))

kb.tell(F(susan, isa, human))


