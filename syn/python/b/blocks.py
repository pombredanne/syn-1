import ast
from functools import partial
from syn.base_utils import setitem, pyversion
from syn.type.a import List
from syn.five import STR, xrange
from .base import PythonNode, Attr, AST, ACO, CC, Statement, Expression, \
    resolve_progn, GenSym, ProgN, AsValue, ResolveProgN, logging
from .literals import Tuple, List as List_
from .statements import Assign
from .variables import Name

VER = pyversion()
OAttr = partial(Attr, optional=True)

#-------------------------------------------------------------------------------
# Block


class Block(Statement):
    _attrs = dict(body = Attr(List((Expression, Statement)), 
                              groups=(AST, ACO, CC)))
    _opts = dict(max_len = 0)

    def emit_block(self, head, body, **kwargs):
        ret = self._indent(**kwargs)
        ret += head + ':\n'

        level = kwargs.get('indent_level', 0)
        with setitem(kwargs, 'indent_level', level + 1):
            strs = [elem.emit(**kwargs) for elem in body]

        ret += '\n'.join(strs)
        return ret

    def valuify_block(self, body, name, **kwargs):
        child = body[-1]
        if isinstance(child, Assign):
            if name in child.targets:
                return

        if not isinstance(child, Expression):
            child = child.as_value(**kwargs).resolve_progn(**kwargs)
        body[-1] = Assign([name], child)


#-------------------------------------------------------------------------------
# If


class If(Block):
    _attrs = dict(test = Attr(Expression, groups=(AST, ACO)),
                  orelse = Attr(List((Expression, Statement)), 
                                groups=(AST, ACO, CC), init=lambda self: list()))
    _opts = dict(args = ('test', 'body', 'orelse'))

    def as_return(self, **kwargs):
        ret = self.copy()
        ret.body[-1] = ret.body[-1].as_return(**kwargs)
        if ret.orelse:
            ret.orelse[-1] = ret.orelse[-1].as_return(**kwargs)
        ret._set_children()
        ret._init()
        return ret

    @logging(AsValue)
    def as_value(self, **kwargs):
        ret = self.copy()

        var = None
        if isinstance(ret.body[-1], Assign):
            var = ret.body[-1].targets[0]
        if var is None and ret.orelse:
            if isinstance(ret.orelse[-1], Assign):
                var = ret.orelse[-1].targets[0]
        if var is None:
            if 'gensym' not in kwargs:
                kwargs['gensym'] = GenSym(ret.variables(**kwargs))
            var = Name(kwargs['gensym'].generate())
            
        ret.valuify_block(ret.body, var, **kwargs)
        if ret.orelse:
            ret.valuify_block(ret.orelse, var, **kwargs)

        ret._set_children()
        ret._init()
        ret._progn_value = var
        return ProgN(ret)

    def emit(self, **kwargs):
        with setitem(kwargs, 'indent_level', 0):
            head = 'if ' + self.test.emit(**kwargs)

        ret = self.emit_block(head, self.body, **kwargs)
        
        if self.orelse:
            head = 'else'
            block = self.emit_block(head, self.orelse, **kwargs)
            ret += '\n' + block

        return ret

    @logging(ResolveProgN)
    def resolve_progn(self, **kwargs):
        temp = self.copy()
        temp.body = resolve_progn(temp.body, **kwargs)
        if temp.orelse:
            temp.orelse = resolve_progn(temp.orelse, **kwargs)
        temp._set_children()
        temp._init()
        kwargs['attr_exclude'] = ['body', 'orelse']
        ret = super(If, temp).resolve_progn(**kwargs)
        return ret


#-------------------------------------------------------------------------------
# For


class For(Block):
    _attrs = dict(target = Attr((Name, Tuple, List_), groups=(AST, ACO)),
                  iter = Attr(Expression, groups=(AST, ACO)),
                  orelse = Attr(List((Expression, Statement)), 
                                groups=(AST, ACO, CC), init=lambda self: list()))
    _opts = dict(args = ('target', 'iter', 'body', 'orelse'))
    
    def emit(self, **kwargs):
        with setitem(kwargs, 'indent_level', 0):
            head = 'for {} in {}'.format(self.target.emit(**kwargs),
                                         self.iter.emit(**kwargs))

        ret = self.emit_block(head, self.body, **kwargs)
        
        if self.orelse:
            head = 'else'
            block = self.emit_block(head, self.orelse, **kwargs)
            ret += '\n' + block

        return ret


#-------------------------------------------------------------------------------
# While


class While(Block):
    _attrs = dict(test = Attr(Expression, groups=(AST, ACO)),
                  orelse = Attr(List((Expression, Statement)), 
                                groups=(AST, ACO, CC), init=lambda self: list()))
    _opts = dict(args = ('test', 'body', 'orelse'))

    def emit(self, **kwargs):
        with setitem(kwargs, 'indent_level', 0):
            head = 'while ' + self.test.emit(**kwargs)

        ret = self.emit_block(head, self.body, **kwargs)
        
        if self.orelse:
            head = 'else'
            block = self.emit_block(head, self.orelse, **kwargs)
            ret += '\n' + block

        return ret


#-------------------------------------------------------------------------------
# Arg


class Arg(PythonNode):
    if VER >= '3':
        ast = ast.arg
    
    _opts = dict(max_len = 0,
                 args = ['arg', 'annotation'])
    _attrs = dict(arg = Attr(STR, group=AST),
                  annotation = OAttr(Expression, groups=(AST, ACO)))

    def emit(self, **kwargs):
        ret = self.arg
        if self.annotation:
            ret += ': {}'.format(self.annotation.emit(**kwargs))
        return ret
        

#-------------------------------------------------------------------------------
# Arguments


class Arguments(PythonNode):
    ast = ast.arguments
    _opts = dict(max_len = 0,
                 args = ['args', 'vararg', 'kwarg', 'defaults'])
    _attrs = dict(args = Attr(List(Name), groups=(AST, ACO, CC)),
                  vararg = OAttr(STR, group=AST),
                  kwarg = OAttr(STR, group=AST),
                  defaults = Attr(List(Expression), groups=(AST, ACO, CC),
                                  init=lambda self: list()))

    if VER >= '3.4':
        _attrs = dict(args = Attr(List(Arg), groups=(AST, ACO, CC)),
                      kwonlyargs = Attr(List(Arg), groups=(AST, ACO, CC),
                                        init=lambda self: list()),
                      vararg = OAttr(Arg, groups=(AST, ACO)),
                      kwarg = OAttr(Arg, groups=(AST, ACO)),
                      defaults = Attr(List(Expression), groups=(AST, ACO, CC),
                                      init=lambda self: list()),
                      kw_defaults = Attr(List((Expression, type(None))), 
                                              groups=(AST, ACO, CC),
                                         init=lambda self: list()))
        _opts['args'] = ['args', 'vararg', 'kwonlyargs', 'kwarg', 
                         'defaults', 'kw_defaults']

    def emit2(self, **kwargs):
        with setitem(kwargs, 'indent_level', 0):
            n_defs = len(self.defaults)
            N = len(self.args) - n_defs
            strs = [self.args[k].emit(**kwargs) for k in xrange(N)]
            strs += ['{}={}'.format(self.args[k + N].emit(**kwargs),
                                    self.defaults[k].emit(**kwargs))
                     for k in xrange(n_defs)]
            if self.vararg:
                strs.append('*' + self.vararg)
            if self.kwarg:
                strs.append('**' + self.kwarg)

        return ', '.join(strs)

    def emit3(self, **kwargs):
        with setitem(kwargs, 'indent_level', 0):
            n_defs = len(self.defaults)
            N = len(self.args) - n_defs
            strs = [self.args[k].emit(**kwargs) for k in xrange(N)]
            strs += ['{}={}'.format(self.args[k + N].emit(**kwargs),
                                    self.defaults[k].emit(**kwargs))
                     for k in xrange(n_defs)]

            if self.vararg:
                strs.append('*' + self.vararg.emit(**kwargs))

            for kwonly, kwonlydef in zip(self.kwonlyargs, self.kw_defaults):
                if kwonlydef is not None:
                    strs.append('{}={}'.format(kwonly.emit(**kwargs),
                                               kwonlydef.emit(**kwargs)))
                else:
                    strs.append(kwonly.emit(**kwargs))

            if self.kwarg:
                strs.append('**' + self.kwarg.emit(**kwargs))
                
        return ', '.join(strs)

    def emit(self, **kwargs):
        if VER >= '3':
            return self.emit3(**kwargs)
        return self.emit2(**kwargs)


#-------------------------------------------------------------------------------
# FunctionDef


class FunctionDef(Block):
    _opts = dict(args = ['name', 'args', 'body', 'decorator_list'])
    _attrs = dict(name = Attr(STR, group=AST),
                  args = Attr(Arguments, groups=(AST, ACO)),
                  decorator_list = OAttr(List(Expression), 
                                         groups=(AST, ACO, CC)))

    if VER >= '3':
        _attrs['returns'] = OAttr(Expression, groups=(AST, ACO))
        _opts['args'].append('returns')

    def emit_decorators(self, **kwargs):
        if not self.decorator_list:
            return ''

        pre = self._indent(**kwargs)
        with setitem(kwargs, 'indent_level', 0):
            strs = [pre + '@' + dec.emit(**kwargs) 
                    for dec in self.decorator_list]
        return '\n'.join(strs) + '\n'
        
    def emit(self, **kwargs):
        ret = self.emit_decorators(**kwargs)
        head = 'def ' + self.name + '(' + self.args.emit(**kwargs) + ')'
        if VER >= '3':
            if self.returns:
                with setitem(kwargs, 'indent_level', 0):
                    head += ' -> {}'.format(self.returns.emit(**kwargs))
        ret += self.emit_block(head, self.body, **kwargs)
        return ret


#-------------------------------------------------------------------------------
# __all__

__all__ = ('Block',
           'If', 'For', 'While',
           'Arg', 'Arguments', 'FunctionDef')

#-------------------------------------------------------------------------------
