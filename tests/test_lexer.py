import unittest

from tinylang.errors import LexError
from tinylang.lexer import tokenize


def kinds_values(src):
    return [(t.kind, t.value) for t in tokenize(src)[:-1]]  # ignora EOF


class LexerTest(unittest.TestCase):
    def test_numeros(self):
        self.assertEqual(kinds_values("42 3.14"), [("NUMBER", 42), ("NUMBER", 3.14)])

    def test_operadores(self):
        vals = [v for _, v in kinds_values("a <= b == c != d")]
        self.assertEqual(vals, ["a", "<=", "b", "==", "c", "!=", "d"])

    def test_keywords_e_identificadores(self):
        self.assertEqual(
            kinds_values("let x"),
            [("KEYWORD", "let"), ("IDENT", "x")],
        )

    def test_string_com_escape(self):
        self.assertEqual(kinds_values(r'"oi\n\"mundo\""'), [("STRING", 'oi\n"mundo"')])

    def test_comentario_ignorado(self):
        self.assertEqual(kinds_values("1 # comentario\n2"), [("NUMBER", 1), ("NUMBER", 2)])

    def test_conta_linhas(self):
        toks = tokenize("a\nb\n\nc")
        self.assertEqual([t.line for t in toks[:-1]], [1, 2, 4])

    def test_string_aberta_da_erro(self):
        with self.assertRaises(LexError):
            tokenize('"sem fim')

    def test_caractere_invalido(self):
        with self.assertRaises(LexError):
            tokenize("a @ b")


if __name__ == "__main__":
    unittest.main()
