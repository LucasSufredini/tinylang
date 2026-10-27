"""Nós da árvore sintática abstrata (AST).

O parser gera esses objetos e o interpretador caminha por eles.
Cada nó guarda a linha para as mensagens de erro em tempo de execução.
"""

from dataclasses import dataclass, field


# ---------- expressões ----------

@dataclass
class Literal:
    value: object
    line: int = 0


@dataclass
class Variable:
    name: str
    line: int = 0


@dataclass
class Assign:
    name: str
    value: object
    line: int = 0


@dataclass
class Unary:
    op: str
    operand: object
    line: int = 0


@dataclass
class Binary:
    left: object
    op: str
    right: object
    line: int = 0


@dataclass
class Logical:
    # separado do Binary porque "and"/"or" fazem curto-circuito
    left: object
    op: str
    right: object
    line: int = 0


@dataclass
class Call:
    callee: object
    args: list
    line: int = 0


@dataclass
class FunctionExpr:
    name: str          # "<anonima>" quando é lambda
    params: list
    body: list
    line: int = 0


# ---------- comandos ----------

@dataclass
class ExprStmt:
    expr: object
    line: int = 0


@dataclass
class Let:
    name: str
    value: object
    line: int = 0


@dataclass
class Block:
    statements: list = field(default_factory=list)
    line: int = 0


@dataclass
class If:
    cond: object
    then: Block
    otherwise: object = None   # Block, If ou None
    line: int = 0


@dataclass
class While:
    cond: object
    body: Block
    line: int = 0


@dataclass
class Return:
    value: object = None
    line: int = 0
