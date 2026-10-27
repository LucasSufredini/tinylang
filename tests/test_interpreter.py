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


class FuncoesTest(unittest.TestCase):
    def test_funcao_simples(self):
        self.assertEqual(run("fn soma(a, b) { return a + b; } soma(2, 3);"), 5)

    def test_sem_return_devolve_nil(self):
        self.assertIsNone(run("fn f() { 1; } f();"))

    def test_recursao(self):
        src = "fn fib(n) { if (n < 2) { return n; } return fib(n-1) + fib(n-2); } fib(15);"
        self.assertEqual(run(src), 610)

    def test_return_dentro_do_while(self):
        src = """
        fn primeiroMaiorQue(lim) {
            let i = 0;
            while (true) { if (i * i > lim) { return i; } i = i + 1; }
        }
        primeiroMaiorQue(50);
        """
        self.assertEqual(run(src), 8)

    def test_closure_contador(self):
        src = """
        fn contador() {
            let n = 0;
            return fn() { n = n + 1; return n; };
        }
        let c = contador();
        c(); c();
        c();
        """
        self.assertEqual(run(src), 3)

    def test_closures_independentes(self):
        src = """
        fn somador(x) { return fn(y) { return x + y; }; }
        let mais10 = somador(10);
        let mais1 = somador(1);
        mais10(5) + mais1(5);
        """
        self.assertEqual(run(src), 21)

    def test_funcao_como_argumento(self):
        src = "fn aplica(f, v) { return f(v); } aplica(fn(x) { return x * 2; }, 21);"
        self.assertEqual(run(src), 42)

    def test_aridade_errada(self):
        with self.assertRaises(RuntimeErr):
            run("fn f(a) { return a; } f(1, 2);")

    def test_chamar_nao_funcao(self):
        with self.assertRaises(RuntimeErr):
            run("let x = 1; x();")

    def test_recursao_infinita(self):
        with self.assertRaises(RuntimeErr):
            run("fn f() { return f(); } f();")

    def test_return_fora_de_funcao(self):
        with self.assertRaises(RuntimeErr):
            run("return 1;")


class BuiltinsTest(unittest.TestCase):
    def test_print(self):
        saida = []
        Interpreter(output=saida.append).run('print("x =", 1, true, nil);')
        self.assertEqual(saida, ["x = 1 true nil"])

    def test_conversoes(self):
        self.assertEqual(run('str(10) + "!";'), "10!")
        self.assertEqual(run('num("3") + 1;'), 4)
        self.assertEqual(run('num("2.5");'), 2.5)
        self.assertEqual(run('len("ufscar");'), 6)
        self.assertEqual(run("type(fn() {});"), "function")

    def test_erro_de_builtin_tem_linha(self):
        with self.assertRaises(RuntimeErr) as ctx:
            run('\n\nnum("abc");')
        self.assertEqual(ctx.exception.line, 3)


if __name__ == "__main__":
    unittest.main()
