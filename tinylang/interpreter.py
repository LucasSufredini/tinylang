"""Interpretador tree-walking: avalia a AST diretamente, nó por nó."""

from . import ast_nodes as ast
from .errors import RuntimeErr
from .parser import parse


class Environment:
    """Escopo de variáveis. Cada bloco cria um novo, apontando para o de fora."""

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def define(self, name, value):
        self.vars[name] = value

    def find(self, name):
        env = self
        while env is not None:
            if name in env.vars:
                return env
            env = env.parent
        return None

    def get(self, name, line):
        env = self.find(name)
        if env is None:
            raise RuntimeErr(f"variável '{name}' não foi definida", line)
        return env.vars[name]

    def assign(self, name, value, line):
        env = self.find(name)
        if env is None:
            raise RuntimeErr(f"variável '{name}' não foi definida (use 'let' antes)", line)
        env.vars[name] = value


class ReturnSignal(Exception):
    """Usado para 'pular' do meio do corpo da função até quem chamou."""

    def __init__(self, value):
        self.value = value


class Function:
    """Função definida pelo usuário. Guarda o ambiente onde foi criada (closure)."""

    def __init__(self, decl, closure):
        self.decl = decl
        self.closure = closure

    def arity(self):
        return len(self.decl.params)

    def call(self, interp, args):
        env = Environment(self.closure)
        for name, value in zip(self.decl.params, args):
            env.define(name, value)
        try:
            interp.execute_block(self.decl.body, env)
        except ReturnSignal as ret:
            return ret.value
        return None

    def __str__(self):
        return f"<fn {self.decl.name}>"


class Builtin:
    """Função nativa, implementada em Python."""

    def __init__(self, name, arity, fn):
        self.name = name
        self._arity = arity  # None = aceita qualquer quantidade
        self.fn = fn

    def arity(self):
        return self._arity

    def call(self, interp, args):
        return self.fn(*args)

    def __str__(self):
        return f"<builtin {self.name}>"


# ---------- helpers de tipo ----------

def is_number(v):
    # bool é subclasse de int em Python, então precisa excluir explicitamente
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def truthy(v):
    # igual Lua/Ruby: só false e nil são falsos
    return v is not None and v is not False


def type_name(v):
    if v is None:
        return "nil"
    if isinstance(v, bool):
        return "bool"
    if is_number(v):
        return "number"
    if isinstance(v, str):
        return "string"
    return "function"


def stringify(v):
    if v is None:
        return "nil"
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def values_equal(a, b):
    if is_number(a) and is_number(b):
        return a == b
    # evita que true == 1 dê verdadeiro como acontece no Python
    return type(a) is type(b) and a == b


class Interpreter:
    def __init__(self, output=print):
        self.output = output
        self.globals = Environment()
        self.define_builtins()

    def define_builtins(self):
        def _print(*args):
            self.output(" ".join(stringify(a) for a in args))

        def _len(s):
            if not isinstance(s, str):
                raise RuntimeErr(f"len() espera string, recebeu {type_name(s)}")
            return len(s)

        def _num(s):
            try:
                return int(s)
            except (TypeError, ValueError):
                try:
                    return float(s)
                except (TypeError, ValueError):
                    raise RuntimeErr(f"não consegui converter {stringify(s)!r} para número")

        for b in (
            Builtin("print", None, _print),
            Builtin("len", 1, _len),
            Builtin("str", 1, stringify),
            Builtin("num", 1, _num),
            Builtin("type", 1, type_name),
            Builtin("input", None, lambda *p: input(*(stringify(x) for x in p))),
        ):
            self.globals.define(b.name, b)

    def run(self, source):
        program = parse(source)
        result = None
        try:
            for stmt in program:
                result = self.execute(stmt, self.globals)
        except RecursionError:
            raise RuntimeErr("estouro de pilha (recursão infinita?)") from None
        except ReturnSignal:
            raise RuntimeErr("'return' fora de função") from None
        return result

    # ---------- comandos ----------

    def execute(self, node, env):
        if isinstance(node, ast.ExprStmt):
            return self.evaluate(node.expr, env)
        if isinstance(node, ast.Let):
            env.define(node.name, self.evaluate(node.value, env))
            return None
        if isinstance(node, ast.Block):
            self.execute_block(node.statements, Environment(env))
            return None
        if isinstance(node, ast.If):
            if truthy(self.evaluate(node.cond, env)):
                self.execute(node.then, env)
            elif node.otherwise is not None:
                self.execute(node.otherwise, env)
            return None
        if isinstance(node, ast.While):
            while truthy(self.evaluate(node.cond, env)):
                self.execute(node.body, env)
            return None
        if isinstance(node, ast.Return):
            value = None if node.value is None else self.evaluate(node.value, env)
            raise ReturnSignal(value)
        raise RuntimeErr(f"comando desconhecido: {type(node).__name__}", node.line)

    def execute_block(self, statements, env):
        for stmt in statements:
            self.execute(stmt, env)

    # ---------- expressões ----------

    def evaluate(self, node, env):
        if isinstance(node, ast.Literal):
            return node.value
        if isinstance(node, ast.Variable):
            return env.get(node.name, node.line)
        if isinstance(node, ast.Assign):
            value = self.evaluate(node.value, env)
            env.assign(node.name, value, node.line)
            return value
        if isinstance(node, ast.Unary):
            return self.unary(node, env)
        if isinstance(node, ast.Logical):
            left = self.evaluate(node.left, env)
            # curto-circuito: nem avalia o lado direito se não precisar
            if node.op == "or" and truthy(left):
                return left
            if node.op == "and" and not truthy(left):
                return left
            return self.evaluate(node.right, env)
        if isinstance(node, ast.Binary):
            return self.binary(node, env)
        if isinstance(node, ast.FunctionExpr):
            return Function(node, env)
        if isinstance(node, ast.Call):
            return self.call(node, env)
        raise RuntimeErr(f"expressão desconhecida: {type(node).__name__}", node.line)

    def call(self, node, env):
        callee = self.evaluate(node.callee, env)
        args = [self.evaluate(a, env) for a in node.args]
        if not isinstance(callee, (Function, Builtin)):
            raise RuntimeErr(f"{type_name(callee)} não é uma função", node.line)
        expected = callee.arity()
        if expected is not None and expected != len(args):
            raise RuntimeErr(
                f"{callee} espera {expected} argumento(s), recebeu {len(args)}", node.line
            )
        try:
            return callee.call(self, args)
        except RuntimeErr as e:
            # builtins não sabem a linha, então completa aqui
            if e.line is None:
                raise RuntimeErr(e.message, node.line) from None
            raise

    def unary(self, node, env):
        value = self.evaluate(node.operand, env)
        if node.op == "!":
            return not truthy(value)
        if not is_number(value):
            raise RuntimeErr(f"não dá pra usar '-' em {type_name(value)}", node.line)
        return -value

    def binary(self, node, env):
        a = self.evaluate(node.left, env)
        b = self.evaluate(node.right, env)
        op = node.op

        if op == "==":
            return values_equal(a, b)
        if op == "!=":
            return not values_equal(a, b)

        if op == "+" and isinstance(a, str) and isinstance(b, str):
            return a + b
        if op == "+" and (isinstance(a, str) or isinstance(b, str)):
            raise RuntimeErr("não dá pra somar string com outro tipo (use str())", node.line)

        if not (is_number(a) and is_number(b)):
            raise RuntimeErr(
                f"operador '{op}' espera números, recebeu {type_name(a)} e {type_name(b)}",
                node.line,
            )

        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op in ("/", "%") and b == 0:
            raise RuntimeErr("divisão por zero", node.line)
        if op == "/":
            # mantém inteiro quando a divisão é exata (6 / 2 == 3, não 3.0)
            if isinstance(a, int) and isinstance(b, int) and a % b == 0:
                return a // b
            return a / b
        if op == "%":
            return a % b
        if op == "<":
            return a < b
        if op == ">":
            return a > b
        if op == "<=":
            return a <= b
        if op == ">=":
            return a >= b
        raise RuntimeErr(f"operador desconhecido '{op}'", node.line)
