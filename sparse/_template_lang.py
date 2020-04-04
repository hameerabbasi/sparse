import ast
import collections
import inspect
import types
import typing
import inspect
import textwrap


def const_expr(x):
    return x


class ConstExprTransformer(ast.NodeTransformer):
    def __init__(self, filename, global_vars=None, local_vars=None):
        if global_vars is None:
            global_vars = {}
        if local_vars is None:
            local_vars = {}
        self.filename: str = filename
        self.global_vars: typing.Dict[str, typing.Any] = global_vars
        self.local_vars: typing.Dict[str, typing.Any] = local_vars

    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        if not isinstance(node.value, ast.Call):
            return node

        if self._partial_eval_ast(node.value.func) is not const_expr:
            return node

        if len(node.targets) != 1:
            return ValueError("Only one target supported for a constexpr assignment.")

        if not isinstance(node.targets[0], ast.Name) or not isinstance(
            node.targets[0].ctx, ast.Store
        ):
            return ValueError(
                "The target of a constexpr assignment must be a variable."
            )

        const = self._partial_eval_ast(node.value)
        self.local_vars[node.targets[0].id] = const

    def visit_If(self, node: ast.If) -> typing.Union[ast.If, typing.List[ast.AST]]:
        if not isinstance(node.test, ast.Call):
            return node

        if self._partial_eval_ast(node.test.func) is not const_expr:
            return node

        const = self._partial_eval_ast(node.test)
        try:
            const = bool(const)
        except TypeError:
            return ValueError("The test of a constexpr if must be castable to `bool`.")

        if const:
            return node.body
        else:
            return node.orelse

    def _partial_eval_ast(self, node):
        expr = ast.Expression(body=node)
        expr = ast.copy_location(expr, node)
        return eval(
            compile(expr, mode="eval", filename=self.filename),
            self.global_vars,
            self.local_vars,
        )


def wrap_constexpr(func):
    frames = inspect.stack()
    caller_frame = frames[1][0]
    global_vars = caller_frame.f_globals.copy()
    local_vars = caller_frame.f_locals.copy()
    filename = caller_frame.f_code.co_filename
    func_source = textwrap.dedent(inspect.getsource(func))
    func_ast = ast.parse(func_source)
    transformer = ConstExprTransformer(
        global_vars=global_vars, local_vars=local_vars, filename=filename
    )
    transformed_func_ast = transformer.visit(func_ast)
    transformed_func_ast.body[0].decorator_list = list(
        filter(
            lambda node: transformer._partial_eval_ast(node) is not wrap_constexpr,
            transformed_func_ast.body[0].decorator_list,
        )
    )
    transformer.global_vars.update(transformer.local_vars)
    exec(
        compile(transformed_func_ast, mode="exec", filename=filename),
        transformer.global_vars,
    )
    print(ast.dump(transformed_func_ast.body[0]))
    return transformer.global_vars[transformed_func_ast.body[0].name]
