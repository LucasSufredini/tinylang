"""Analisador léxico: transforma o texto do programa em uma lista de tokens.

Funciona como um autômato finito escrito "na mão": olhamos o caractere atual
e decidimos em qual estado entrar (número, identificador, string, operador...).
"""

from dataclasses import dataclass

from .errors import LexError

KEYWORDS = {
    "let", "fn", "return", "if", "else", "while",
    "true", "false", "nil", "and", "or", "not",
}

# operadores de dois caracteres precisam ser testados antes dos de um
TWO_CHAR_OPS = {"==", "!=", "<=", ">="}
ONE_CHAR_OPS = set("+-*/%<>=(){},;!")


@dataclass
class Token:
    kind: str      # NUMBER, STRING, IDENT, KEYWORD, OP, EOF
    value: object
    line: int

    def __repr__(self):
        return f"Token({self.kind}, {self.value!r}, linha={self.line})"


class Lexer:
    def __init__(self, source):
        self.src = source
        self.pos = 0
        self.line = 1

    def peek(self, offset=0):
        i = self.pos + offset
        return self.src[i] if i < len(self.src) else "\0"

    def advance(self):
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
        return ch

    def tokenize(self):
        tokens = []
        while self.pos < len(self.src):
            ch = self.peek()

            if ch in " \t\r\n":
                self.advance()
            elif ch == "#":
                # comentário vai até o fim da linha
                while self.pos < len(self.src) and self.peek() != "\n":
                    self.advance()
            elif ch.isdigit():
                tokens.append(self.number())
            elif ch.isalpha() or ch == "_":
                tokens.append(self.identifier())
            elif ch == '"':
                tokens.append(self.string())
            elif ch + self.peek(1) in TWO_CHAR_OPS:
                op = self.advance() + self.advance()
                tokens.append(Token("OP", op, self.line))
            elif ch in ONE_CHAR_OPS:
                tokens.append(Token("OP", self.advance(), self.line))
            else:
                raise LexError(f"caractere inesperado {ch!r}", self.line)

        tokens.append(Token("EOF", None, self.line))
        return tokens

    def number(self):
        start = self.pos
        while self.peek().isdigit():
            self.advance()
        # só vira float se tiver dígito depois do ponto (ex: 3.14)
        if self.peek() == "." and self.peek(1).isdigit():
            self.advance()
            while self.peek().isdigit():
                self.advance()
            return Token("NUMBER", float(self.src[start:self.pos]), self.line)
        return Token("NUMBER", int(self.src[start:self.pos]), self.line)

    def identifier(self):
        start = self.pos
        while self.peek().isalnum() or self.peek() == "_":
            self.advance()
        word = self.src[start:self.pos]
        kind = "KEYWORD" if word in KEYWORDS else "IDENT"
        return Token(kind, word, self.line)

    def string(self):
        line = self.line
        self.advance()  # pula a aspa de abertura
        chars = []
        escapes = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
        while self.peek() != '"':
            if self.pos >= len(self.src):
                raise LexError("string não foi fechada", line)
            ch = self.advance()
            if ch == "\\":
                nxt = self.advance()
                chars.append(escapes.get(nxt, nxt))
            else:
                chars.append(ch)
        self.advance()  # aspa de fechamento
        return Token("STRING", "".join(chars), line)


def tokenize(source):
    return Lexer(source).tokenize()
