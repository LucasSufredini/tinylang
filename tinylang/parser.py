"""Parser descendente recursivo.

Cada regra da gramática (ver GRAMMAR.md) virou um método. A precedência dos
operadores sai naturalmente da ordem em que os métodos chamam uns aos outros:
quanto mais "embaixo" na cadeia, mais forte o operador.
"""

from . import ast_nodes as ast
from .errors import ParseError
from .lexer import tokenize


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ---------- utilitários ----------

    def peek(self, offset=0):
        i = min(self.pos + offset, len(self.tokens) - 1)
        return self.tokens[i]

    def at_end(self):
        return self.peek().kind == "EOF"

    def check(self, kind, value=None):
        tok = self.peek()
        return tok.kind == kind and (value is None or tok.value == value)

    def match(self, kind, *values):
        """Consome o token se ele for de um dos valores pedidos."""
        tok = self.peek()
        if tok.kind == kind and (not values or tok.value in values):
            self.pos += 1
            return tok
        return None

    def expect(self, kind, value=None, msg=None):
        if self.check(kind, value):
            tok = self.peek()
            self.pos += 1
            return tok
        tok = self.peek()
        got = "fim do arquivo" if tok.kind == "EOF" else repr(tok.value)
        raise ParseError(msg or f"esperava {value or kind}, encontrei {got}", tok.line)

    # ---------- comandos ----------

    def parse(self):
        stmts = []
        while not self.at_end():
            stmts.append(self.statement())
        return stmts

    def statement(self):
        if self.check("KEYWORD", "let"):
            return self.let_stmt()
        # "fn nome(...)" é declaração; "fn(...)" sozinho é expressão (lambda)
        if self.check("KEYWORD", "fn") and self.peek(1).kind == "IDENT":
            return self.fn_decl()
        if self.check("KEYWORD", "if"):
            return self.if_stmt()
        if self.check("KEYWORD", "while"):
            return self.while_stmt()
        if self.check("KEYWORD", "return"):
            return self.return_stmt()
        if self.check("OP", "{"):
            return self.block()
        line = self.peek().line
        expr = self.expression()
        self.expect("OP", ";", "faltou ';' no fim do comando")
        return ast.ExprStmt(expr, line)

    def let_stmt(self):
        line = self.expect("KEYWORD", "let").line
        name = self.expect("IDENT", msg="esperava nome da variável depois de 'let'").value
        self.expect("OP", "=")
        value = self.expression()
        self.expect("OP", ";", "faltou ';' no fim do comando")
        return ast.Let(name, value, line)

    def fn_decl(self):
        line = self.expect("KEYWORD", "fn").line
        name = self.expect("IDENT").value
        fn = self.function_rest(name, line)
        # açúcar sintático: "fn f() {}" é o mesmo que "let f = fn() {};"
        return ast.Let(name, fn, line)

    def function_rest(self, name, line):
        self.expect("OP", "(")
        params = []
        if not self.check("OP", ")"):
            while True:
                params.append(self.expect("IDENT", msg="esperava nome de parâmetro").value)
                if not self.match("OP", ","):
                    break
        self.expect("OP", ")")
        body = self.block().statements
        return ast.FunctionExpr(name, params, body, line)

    def if_stmt(self):
        line = self.expect("KEYWORD", "if").line
        self.expect("OP", "(")
        cond = self.expression()
        self.expect("OP", ")")
        then = self.block()
        otherwise = None
        if self.match("KEYWORD", "else"):
            otherwise = self.if_stmt() if self.check("KEYWORD", "if") else self.block()
        return ast.If(cond, then, otherwise, line)

    def while_stmt(self):
        line = self.expect("KEYWORD", "while").line
        self.expect("OP", "(")
        cond = self.expression()
        self.expect("OP", ")")
        return ast.While(cond, self.block(), line)

    def return_stmt(self):
        line = self.expect("KEYWORD", "return").line
        value = None
        if not self.check("OP", ";"):
            value = self.expression()
        self.expect("OP", ";", "faltou ';' depois do return")
        return ast.Return(value, line)

    def block(self):
        line = self.expect("OP", "{").line
        stmts = []
        while not self.check("OP", "}"):
            if self.at_end():
                raise ParseError("bloco não foi fechado com '}'", line)
            stmts.append(self.statement())
        self.expect("OP", "}")
        return ast.Block(stmts, line)

    # ---------- expressões (da menor para a maior precedência) ----------

    def expression(self):
        return self.assignment()

    def assignment(self):
        expr = self.logic_or()
        if self.check("OP", "="):
            line = self.peek().line
            self.pos += 1
            value = self.assignment()  # recursão à direita: a = b = 1
            if isinstance(expr, ast.Variable):
                return ast.Assign(expr.name, value, line)
            raise ParseError("lado esquerdo da atribuição precisa ser uma variável", line)
        return expr

    def logic_or(self):
        expr = self.logic_and()
        while tok := self.match("KEYWORD", "or"):
            expr = ast.Logical(expr, "or", self.logic_and(), tok.line)
        return expr

    def logic_and(self):
        expr = self.equality()
        while tok := self.match("KEYWORD", "and"):
            expr = ast.Logical(expr, "and", self.equality(), tok.line)
        return expr

    def binary_level(self, next_level, *ops):
        """Regra genérica para operadores binários associativos à esquerda."""
        expr = next_level()
        while tok := self.match("OP", *ops):
            expr = ast.Binary(expr, tok.value, next_level(), tok.line)
        return expr

    def equality(self):
        return self.binary_level(self.comparison, "==", "!=")

    def comparison(self):
        return self.binary_level(self.term, "<", ">", "<=", ">=")

    def term(self):
        return self.binary_level(self.factor, "+", "-")

    def factor(self):
        return self.binary_level(self.unary, "*", "/", "%")

    def unary(self):
        if tok := (self.match("OP", "-", "!") or self.match("KEYWORD", "not")):
            op = "!" if tok.value == "not" else tok.value
            return ast.Unary(op, self.unary(), tok.line)
        return self.call()

    def call(self):
        expr = self.primary()
        while tok := self.match("OP", "("):
            args = []
            if not self.check("OP", ")"):
                while True:
                    args.append(self.expression())
                    if not self.match("OP", ","):
                        break
            self.expect("OP", ")", "faltou ')' na chamada de função")
            expr = ast.Call(expr, args, tok.line)
        return expr

    def primary(self):
        tok = self.peek()
        if tok.kind in ("NUMBER", "STRING"):
            self.pos += 1
            return ast.Literal(tok.value, tok.line)
        if tok.kind == "KEYWORD" and tok.value in ("true", "false", "nil"):
            self.pos += 1
            value = {"true": True, "false": False, "nil": None}[tok.value]
            return ast.Literal(value, tok.line)
        if tok.kind == "IDENT":
            self.pos += 1
            return ast.Variable(tok.value, tok.line)
        if self.match("KEYWORD", "fn"):
            return self.function_rest("<anonima>", tok.line)
        if self.match("OP", "("):
            expr = self.expression()
            self.expect("OP", ")", "faltou ')'")
            return expr
        got = "fim do arquivo" if tok.kind == "EOF" else repr(tok.value)
        raise ParseError(f"expressão inválida perto de {got}", tok.line)


def parse(source):
    return Parser(tokenize(source)).parse()
