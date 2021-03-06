import collections
from nose.tools import assert_raises
from syn.sets import SetWrapper, TypeWrapper
from syn.util.constraint import Domain, Constraint, Problem

#-------------------------------------------------------------------------------
# Domain

def test_domain():
    d = Domain()
    d['a'] = [1]
    assert d['a'] == SetWrapper([1])
    assert list(d) == ['a']
    d['a'] = int
    assert d['a'] == TypeWrapper(int)
    del d['a']
    assert list(d) == []

    d = Domain(a = [1,2], b = [3,4])
    assert d['a'] == SetWrapper([1, 2])
    assert d['b'] == SetWrapper([3, 4])
    assert d['a'].to_set() == {1, 2}

    assert isinstance(d, collections.Mapping)

    d = Domain(a = [1], b = int)
    assert d.display() == 'Domain(a = {1},\n       b = TypeWrapper(int))'

#-------------------------------------------------------------------------------
# Constraint

def test_constraint():
    c = Constraint()
    assert_raises(NotImplementedError, c.check)
    assert c.display() is None
    assert c.preprocess({}) is None

#-------------------------------------------------------------------------------
# Problem

def test_problem():
    c1 = Constraint(['a'])
    c2 = Constraint(['a', 'b'])
    p = Problem(Domain(a=[1, 2], b=[2, 3]), [c1, c2])
    
    assert p.var_constraint == dict(a = {c1, c2},
                                    b = {c2})

    assert_raises(ValueError, Problem, Domain(a=[1]), [c1, c2])

    from syn.util.constraint import EqualConstraint
    c1 = EqualConstraint('a', 1)
    p = Problem(Domain(a=[1]), [c1])
    assert p.display() == 'Domain(a = {1})\na == 1'

#-------------------------------------------------------------------------------

if __name__ == '__main__': # pragma: no cover
    from syn.base_utils import run_all_tests
    run_all_tests(globals(), verbose=True, print_errors=False)
