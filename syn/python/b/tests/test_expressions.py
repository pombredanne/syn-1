from syn.python.b import Expr

#-------------------------------------------------------------------------------
# Expr

def test_expr():
    Expr

#-------------------------------------------------------------------------------

if __name__ == '__main__': # pragma: no cover
    from syn.base_utils import run_all_tests
    run_all_tests(globals(), verbose=True, print_errors=False)