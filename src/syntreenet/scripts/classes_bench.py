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

# Copyright (c) 2019 by Enrique Pérez Arnaud <enrique@cazalla.net>
#
# This file is part of the syntreenet project.
# https://syntree.net
#
import os
import argparse
from dataclasses import dataclass
from random import randrange
from timeit import timeit
from ..kbase import KnowledgeBase


HERE = os.path.abspath(os.path.dirname(__file__))

sets = ('thing', 'animal', 'mammal', 'primate', 'human',
        'vegetable', 'tree', 'pine')

parser = argparse.ArgumentParser(description='Benchmark on classes.peg.')
parser.add_argument('-n', dest='n' ,type=int,
                    help='number of sentences to add')

@dataclass
class Benchmark:
    n : int
    kb : KnowledgeBase

    def __call__(self):
        kb.tell("X1 is X2 ; X2 is X3 -> X1 is X3")
        kb.tell("X1 isa X2 ; X2 is X3 -> X1 isa X3")
        kb.tell('animal is thing')
        kb.tell('mammal is animal')
        kb.tell('primate is mammal')
        kb.tell('human is primate')
        kb.tell('vegetable is thing')
        kb.tell('tree is vegetable')
        kb.tell('pine is tree')
        l = len(sets)
        for i in range(self.n):
            s = sets[i % l]
            fact = f'{s}{i} isa {s}'
            kb.tell(fact)

if __name__ == '__main__':
    fn = os.path.join(HERE, '../../grammars/classes.peg')
    with open(fn, 'r') as fh:
        kb = KnowledgeBase(fh.read())
    args = parser.parse_args()
    t = timeit(Benchmark(args.n, kb), number=1)
    print(f'took {t}sec to proccess {kb.counter} activations\n'
          f'    mean for activation : {(t/kb.counter)*1000}ms\n'
          f'    mean for added fact : {(t/args.n)*1000}ms')
