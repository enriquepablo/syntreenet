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
import argparse
from dataclasses import dataclass
from random import randrange
from timeit import timeit
from ..babel import ont as o


sets = (o.thing, o.living, o.animal, o.mammal, o.primate, o.human, o.man)

parser = argparse.ArgumentParser(description='Benchmark on ont.')
parser.add_argument('-n', dest='n' ,type=int,
                    help='number of sentences to add')

@dataclass
class Benchmark:
    n : int

    def __call__(self):
        for i in range(self.n):
            s = sets[randrange(len(sets))]
            name = f'{s.name}{i}'
            word = o.Word(name)
            sen = o.Sen(word, o.isa, s)
            o.r.tell(sen)

if __name__ == '__main__':
    args = parser.parse_args()
    t = timeit(Benchmark(args.n), number=1)
    print(f'took {t} s to proccess {o.r.counter} activations\n'
          f'    mean for activation : {(t/o.r.counter)*1000}ms')
