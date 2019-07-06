# -*- coding: utf-8 -*-
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
'''
This script is for Python 2, pyclips is Python 2.7 only.
'''


import argparse
from random import randrange
from timeit import timeit
import clips


sets = ('thing', 'animal', 'mammal', 'primate', 'human')

parser = argparse.ArgumentParser(description='Benchmark on ont.')
parser.add_argument('-n', dest='n' ,type=int,
                    help='number of sentences to add')
parser.add_argument('-b', dest='b' ,type=int,
                    help='batch of facts to run')

class Benchmark:

    def __init__(self, n, b=1):
        self.n = n
        self.b = b

    def __call__(self):
        clips.BuildRule("one", "(is-a ?x1 ?x2) (a-is-a ?x2 ?x3)", "(assert (is-a ?x1 ?x3))", "belogns")
        clips.BuildRule("two", "(a-is-a ?x1 ?x2) (a-is-a ?x2 ?x3)", "(assert (a-is-a ?x1 ?x3))", "subset")
        l = len(sets)
        for i in range(self.n):
            s = sets[i % l]
            name = '%s%d' % (s, i)
            clips.Assert("(is-a %s %s)" % (name, s))
            if self.n % self.b == 0:
                clips.Run()

if __name__ == '__main__':
    args = parser.parse_args()
    t = timeit(Benchmark(args.n, args.b), number=1)
    print('took %f sec to proccess %d facts\n'
          '    mean for added fact : %f ms' % (t, args.n, (float(t)/args.n)*1000))

