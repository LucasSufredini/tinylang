# TinyLang

Um interpretador para uma linguagem de programação pequena, escrito em Python puro
(sem nenhuma dependência). Fiz o projeto para entender na prática o que vemos em
Compiladores e Linguagens Formais: análise léxica, gramáticas livres de contexto,
parsing e execução.

```
fn contador() {
    let n = 0;
    return fn() { n = n + 1; return n; };
}

let c = contador();
c(); c();
print("contei", c(), "vezes");   # contei 3 vezes
```

## O que a linguagem tem

- números (inteiros e reais), strings, `true`/`false` e `nil`
- variáveis com `let` e escopo de bloco
- `if` / `else if` / `else` e `while`
- operadores aritméticos, de comparação e lógicos (`and`/`or` com curto-circuito)
- funções com recursão, funções anônimas e **closures**
- funções nativas: `print`, `len`, `str`, `num`, `type`, `input`
- mensagens de erro com o número da linha
- REPL interativo

## Como rodar

Precisa de Python 3.8 ou mais novo.

```bash
# REPL
python -m tinylang

# executar um arquivo
python -m tinylang examples/fibonacci.tl

# testes
python -m unittest discover -s tests -t .
```

## Como funciona

O código passa por três etapas:

```
texto do programa ──► Lexer ──► tokens ──► Parser ──► AST ──► Interpreter ──► resultado
```

| Arquivo | O que faz |
|---|---|
| `tinylang/lexer.py` | Lê o texto caractere por caractere e gera tokens (`NUMBER`, `IDENT`, `OP`...). Na prática é um autômato finito escrito à mão. |
| `tinylang/parser.py` | Parser **descendente recursivo**: cada regra da gramática vira um método. A precedência dos operadores vem da ordem em que os métodos chamam uns aos outros. A gramática completa está em [GRAMMAR.md](GRAMMAR.md). |
| `tinylang/ast_nodes.py` | As classes da árvore sintática abstrata. |
| `tinylang/interpreter.py` | Interpretador *tree-walking*: percorre a AST e avalia cada nó. Os escopos são uma cadeia de `Environment`s e cada função guarda o ambiente onde foi criada, e é isso que faz as closures funcionarem. |

Algumas decisões que tomei:

- **`return` é implementado com exceção.** Quando o interpretador encontra um `return`
  no meio de um `while` dentro de um `if`, ele precisa sair de várias chamadas
  recursivas de uma vez, e lançar uma exceção capturada em `Function.call` foi o jeito
  mais simples.
- **Só `false` e `nil` são falsos** (igual Lua e Ruby). `0` e `""` são verdadeiros.
- **`true == 1` é falso.** Em Python isso dá `True` porque `bool` herda de `int`, então
  precisei tratar isso separadamente.
- **`6 / 2` dá `3` e não `3.0`**: a divisão continua inteira quando é exata.

## Próximos passos

- [ ] listas e índices (`[1, 2, 3]`, `l[0]`)
- [ ] `for` e `break`/`continue`
- [ ] passo de resolução de variáveis antes da execução (análise semântica)
- [ ] compilar para bytecode e rodar numa máquina virtual de pilha

## Referências

- Robert Nystrom, *Crafting Interpreters* — principal referência para a estrutura do projeto
- Aho, Lam, Sethi, Ullman, *Compiladores: Princípios, Técnicas e Ferramentas* (o "livro do dragão")

Usei IA como apoio durante o desenvolvimento para tirar dúvidas e revisar código.
