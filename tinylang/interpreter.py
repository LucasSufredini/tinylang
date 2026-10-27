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

    def run(self, source):
        program = parse(source)
        result = None
        for stmt in program:
            result = self.execute(stmt, self.globals)
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
        raise RuntimeErr(f"expressão desconhecida: {type(node).__name__}", node.line)

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
