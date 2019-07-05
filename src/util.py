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

from typing import List, Any
try:
    import pygraphviz as PG
except ImportError:
    PG = None


def get_parents(node : Any) -> List[Any]:
    parents = []
    while node is not None:
        parents.append(node)
        node = node.parent
    return parents


def _draw_node(node, nodename, graph):
    for child in node.children.values():
        childname = str(node)
        graph.add_edge(nodename, childname)
        _draw_node(child, childname, graph)
    if hasattr(node, 'var_children'):
        for child in node.var_children.values():
            childname = str(child)
            graph.add_edge(nodename, childname)
            _draw_node(child, childname, graph)
    if hasattr(node, 'var_child') and node.var_child:
        childname = str(node.var_child)
        graph.add_edge(nodename, childname)
        _draw_node(node.var_child, childname, graph)
    if hasattr(node, 'endnode') and node.endnode is not None:
        graph.add_edge(nodename, f'end: {node.endnode}')

def draw_net(root, name):
    if PG is None:
        print('pygraphviz not availbale, aborting.')
        return

    graph = PG.AGraph(directed=True, strict=True)
    _draw_node(root, str(root), graph)

    # save the graph in dot format
    # pygraphviz renders graphs in neato by default, 
    # so you need to specify dot as the layout engine
    graph.layout(prog='dot')
    graph.write(f'{name}.dot')


def print_tree(root):
    pass
