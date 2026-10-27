import unittest

from tinylang import ast_nodes as ast
from tinylang.errors import ParseError
from tinylang.parser import parse


def expr(src):
    """Faz o parse de uma única expressão (adiciona o ';')."""
    return parse(src + ";")[0].expr


class ParserTest(unittest.TestCase):
    def test_precedencia_mult_antes_da_soma(self):
        e = expr("1 + 2 * 3")
        self.assertIsInstance(e, ast.Binary)
        self.assertEqual(e.op, "+")
        self.assertEqual(e.right.op, "*")

    def test_associatividade_esquerda(self):
        # 10 - 3 - 2 tem que ser (10 - 3) - 2
        e = expr("10 - 3 - 2")
        self.assertEqual(e.op, "-")
        self.assertIsInstance(e.left, ast.Binary)
        self.assertEqual(e.right.value, 2)

    def test_parenteses(self):
        e = expr("(1 + 2) * 3")
        self.assertEqual(e.op, "*")
        self.assertEqual(e.left.op, "+")

    def test_atribuicao_associa_a_direita(self):
        e = expr("a = b = 1")
        self.assertIsInstance(e, ast.Assign)
        self.assertIsInstance(e.value, ast.Assign)

    def test_and_or(self):
        e = expr("a or b and c")
        self.assertEqual(e.op, "or")
        self.assertEqual(e.right.op, "and")

    def test_chamada_encadeada(self):
        e = expr("f(1)(2)")
        self.assertIsInstance(e, ast.Call)
        self.assertIsInstance(e.callee, ast.Call)

    def test_declaracao_de_funcao_vira_let(self):
        stmt = parse("fn soma(a, b) { return a + b; }")[0]
        self.assertIsInstance(stmt, ast.Let)
        self.assertEqual(stmt.value.params, ["a", "b"])

    def test_if_else_if(self):
        stmt = parse("if (x) { } else if (y) { } else { }")[0]
        self.assertIsInstance(stmt.otherwise, ast.If)
        self.assertIsInstance(stmt.otherwise.otherwise, ast.Block)

    def test_faltou_ponto_e_virgula(self):
        with self.assertRaises(ParseError):
            parse("let x = 1")

    def test_atribuicao_invalida(self):
        with self.assertRaises(ParseError):
            parse("1 = 2;")

    def test_bloco_aberto(self):
        with self.assertRaises(ParseError):
            parse("while (true) { let x = 1;")


if __name__ == "__main__":
    unittest.main()
