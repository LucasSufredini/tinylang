import unittest

from tinylang.errors import RuntimeErr
from tinylang.interpreter import Interpreter


def run(src):
    """Roda o programa e devolve o valor da última expressão."""
    return Interpreter(output=lambda *_: None).run(src)


class ExpressoesTest(unittest.TestCase):
    def test_aritmetica(self):
        self.assertEqual(run("1 + 2 * 3;"), 7)
        self.assertEqual(run("(1 + 2) * 3;"), 9)
        self.assertEqual(run("10 % 3;"), 1)
        self.assertEqual(run("-2 * 3;"), -6)

    def test_divisao_mantem_inteiro_quando_exata(self):
        self.assertEqual(run("6 / 2;"), 3)
        self.assertIsInstance(run("6 / 2;"), int)
        self.assertEqual(run("7 / 2;"), 3.5)

    def test_divisao_por_zero(self):
        with self.assertRaises(RuntimeErr):
            run("1 / 0;")

    def test_strings(self):
        self.assertEqual(run('"ab" + "cd";'), "abcd")
        with self.assertRaises(RuntimeErr):
            run('"a" + 1;')

    def test_comparacao_e_igualdade(self):
        self.assertIs(run("1 < 2;"), True)
        self.assertIs(run("1 == 1.0;"), True)
        self.assertIs(run("true == 1;"), False)
        self.assertIs(run('"a" != "b";'), True)

    def test_logica_curto_circuito(self):
        # se o "or" avaliasse o lado direito, daria erro de variável
        self.assertIs(run("true or naoExiste;"), True)
        self.assertIs(run("false and naoExiste;"), False)
        self.assertEqual(run("nil or 5;"), 5)

    def test_not(self):
        self.assertIs(run("not nil;"), True)
        self.assertIs(run("!0;"), False)  # 0 é verdadeiro na TinyLang


class VariaveisTest(unittest.TestCase):
    def test_let_e_atribuicao(self):
        self.assertEqual(run("let x = 1; x = x + 1; x;"), 2)

    def test_variavel_inexistente(self):
        with self.assertRaises(RuntimeErr):
            run("y;")

    def test_atribuir_sem_let_da_erro(self):
        with self.assertRaises(RuntimeErr):
            run("y = 1;")

    def test_escopo_de_bloco(self):
        src = """
        let x = "fora";
        { let x = "dentro"; }
        x;
        """
        self.assertEqual(run(src), "fora")

    def test_bloco_altera_variavel_de_fora(self):
        self.assertEqual(run("let x = 1; { x = 2; } x;"), 2)


class ControleTest(unittest.TestCase):
    def test_if_else(self):
        src = "let r = 0; if (1 > 2) { r = 1; } else if (true) { r = 2; } else { r = 3; } r;"
        self.assertEqual(run(src), 2)

    def test_while(self):
        src = "let i = 0; let soma = 0; while (i < 5) { soma = soma + i; i = i + 1; } soma;"
        self.assertEqual(run(src), 10)


if __name__ == "__main__":
    unittest.main()
