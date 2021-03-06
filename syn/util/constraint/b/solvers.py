from .base import Problem
from random import choice
from contextlib import contextmanager
from syn.base import Base, Attr
from syn.sets import Product, Difference
from syn.base_utils import assign

#-------------------------------------------------------------------------------
# Solver


class Solver(Base):
    _attrs = dict(problem = Attr(Problem))
    _opts = dict(init_validate = True,
                 args = ('problem',))

    def solutions(self, **kwargs):
        raise NotImplementedError


#-------------------------------------------------------------------------------
# Simple


class SimpleSolver(Solver):
    '''Enumerates through all possible solutions.  Do not use for any substantially-sized domains!!!
    '''
    def solutions(self, **kwargs):
        vars = sorted(self.problem.var_constraint)
        p = Product(*[self.problem.domain[var] for var in vars])
        for prod in p.lazy_enumerate(**kwargs):
            theory = dict(zip(vars, prod))
            for con in self.problem.constraints:
                if not con.check(**theory):
                    break
            else:
                yield theory


#-------------------------------------------------------------------------------
# Recursive Backtrack


class RecursiveBacktrackSolver(Solver):
    _attrs = dict(forward_checking = Attr(bool, True),
                  selection_method = Attr(['mrv', 'random'], 'mrv'))

    def choose_var(self, uvars, **kwargs):
        if self.selection_method == 'mrv':
            doms = {var: self.problem.domain[var] for var in uvars}
            sort = sorted(doms.items(), 
                          key=lambda pair: pair[1].expected_size())
            return sort[0][0]
        return choice(list(uvars))

    @contextmanager
    def forward_check(self, **kwargs):
        if not self.forward_checking:
            yield

        else:
            theory = kwargs['theory']
            vars = set(theory)
            dom = self.problem.domain.copy()
            one_left_cons = [con for con in self.problem.constraints
                             if len(set(con.args) - vars) == 1]

            for con in one_left_cons:
                th = dict(theory)
                var = (set(con.args) - vars).pop()
                
                vals = []
                for val in dom[var].lazy_enumerate(**kwargs):
                    th[var] = val
                    if not con.check(**th):
                        vals.append(val)

                if vals:
                    dom[var] = Difference(dom[var], vals)

            with assign(self.problem, 'domain', dom):
                yield

    def solutions(self, **kwargs):
        theory = dict(kwargs.get('theory', {}))
        vars = sorted(self.problem.var_constraint)
        uvars = set(vars) - set(theory) # unassigned variables

        if not uvars:
            yield theory

        else:
            var = self.choose_var(uvars, **kwargs)
            for val in self.problem.domain[var].lazy_enumerate(**kwargs):
                theory[var] = val
                kwargs['theory'] = theory
                with self.forward_check(**kwargs):
                    if not self.problem.check(theory):
                        break
                    else:
                        for sol in self.solutions(**kwargs):
                            yield sol


#-------------------------------------------------------------------------------
# __all__

__all__ = ('Solver', 'SimpleSolver', 'RecursiveBacktrackSolver')

#-------------------------------------------------------------------------------
