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

from .grammar import Segment, Matching


class ec_handlers:
    '''
    these functions return False, True, or a new matching dict
    '''

    @staticmethod
    def logic(text, matching, kb):
        tree = kb.parse(text)
        ec = kb.from_parse_tree(tree)
        new_ec = ec.substitute(matching, kb)
        return kb.ask(new_ec)

    @staticmethod
    def python(text, matching, kb):
        exec_globals = {}  # TODO some method to inject 3rd party modules here
        pre_exec_locals = matching.to_dict()
        exec_locals = {}
        for k,v in pre_exec_locals.items():
            try:
                exec_locals[k] = float(v)
            except ValueError:
                exec_locals[k] = v
        try:
            return eval(text, exec_globals, exec_locals)
        except SyntaxError:
            try:
                exec(text, exec_globals, exec_locals)
            except Exception:
                return False
            if 'test' in exec_locals and exec_locals['test'] is False:
                return False
            new_mapping = tuple((Segment(k, '__var__'), Segment(str(v)))
                    for k, v in exec_locals.items() if k not in pre_exec_locals)
            return [Matching(new_mapping)]
