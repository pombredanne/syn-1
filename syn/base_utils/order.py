from collections import defaultdict

#-------------------------------------------------------------------------------
# Special Orders

class First(object):
    pass

class Last(object):
    pass

#-------------------------------------------------------------------------------
# Order Relations


class LE(object):
    def __init__(self, A, B):
        self.A = A
        self.B = B


#-------------------------------------------------------------------------------
# Utilities

def _nodes(relations):
    ret = set()
    for rel in relations:
        ret.add(rel.A)
        ret.add(rel.B)
    return ret

def _incoming(relations):
    ret = defaultdict(set)
    for rel in relations:
        ret[rel.B].add(rel.A)
    return ret

def _outgoing(relations):
    ret = defaultdict(set)
    for rel in relations:
        ret[rel.A].add(rel.B)
    return ret

def _is_free(node, edges):
    return not edges[node]

def _free_nodes(nodes, edges):
    return {node for node in nodes if _is_free(node, edges)}

#-------------------------------------------------------------------------------
# Topological Sort

def topological_sorting(relations):
    '''An implementation of Kahn's algorithm.
    '''
    ret = []
    nodes = _nodes(relations)
    inc = _incoming(relations)
    out = _outgoing(relations)
    free = _free_nodes(nodes, inc)

    if First in nodes:
        if not _is_free(First, inc):
            raise ValueError("Node First has incoming edge")
    
    if Last in nodes:
        if not _is_free(Last, out):
            raise ValueError("Node Last has outgoing edge")

    while free:
        n = free.pop()
        ret.append(n)
        
        out_n = list(out[n])
        for m in out_n:
            out[n].remove(m)
            inc[m].remove(n)
            if _is_free(m, inc):
                free.add(m)

    if not all(_is_free(node, inc) and _is_free(node, out) for node in nodes):
        raise ValueError("Cycle detected")

    if First in ret:
        ret.remove(First)
    if Last in ret:
        ret.remove(Last)
    return ret

#-------------------------------------------------------------------------------
# __all__

__all__ = ('First', 'Last', 'LE',
           'topological_sorting',)

#-------------------------------------------------------------------------------