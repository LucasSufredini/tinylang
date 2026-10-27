# Gramática do TinyLang

Notação EBNF: `*` = zero ou mais, `?` = opcional, `|` = alternativa.
Cada regra corresponde a um método em `tinylang/parser.py`.

```ebnf
program     = statement* EOF ;

statement   = letStmt | fnDecl | ifStmt | whileStmt
            | returnStmt | block | exprStmt ;

letStmt     = "let" IDENT "=" expression ";" ;
fnDecl      = "fn" IDENT "(" params? ")" block ;
ifStmt      = "if" "(" expression ")" block ( "else" ( ifStmt | block ) )? ;
whileStmt   = "while" "(" expression ")" block ;
returnStmt  = "return" expression? ";" ;
block       = "{" statement* "}" ;
exprStmt    = expression ";" ;

expression  = assignment ;
assignment  = IDENT "=" assignment | logic_or ;
logic_or    = logic_and ( "or" logic_and )* ;
logic_and   = equality ( "and" equality )* ;
equality    = comparison ( ( "==" | "!=" ) comparison )* ;
comparison  = term ( ( "<" | ">" | "<=" | ">=" ) term )* ;
term        = factor ( ( "+" | "-" ) factor )* ;
factor      = unary ( ( "*" | "/" | "%" ) unary )* ;
unary       = ( "-" | "!" | "not" ) unary | call ;
call        = primary ( "(" args? ")" )* ;
primary     = NUMBER | STRING | "true" | "false" | "nil" | IDENT
            | "fn" "(" params? ")" block
            | "(" expression ")" ;

params      = IDENT ( "," IDENT )* ;
args        = expression ( "," expression )* ;
```

## Precedência (da mais fraca para a mais forte)

| Nível | Operadores            | Associatividade |
|-------|-----------------------|-----------------|
| 1     | `=`                   | direita         |
| 2     | `or`                  | esquerda        |
| 3     | `and`                 | esquerda        |
| 4     | `==` `!=`             | esquerda        |
| 5     | `<` `>` `<=` `>=`     | esquerda        |
| 6     | `+` `-`               | esquerda        |
| 7     | `*` `/` `%`           | esquerda        |
| 8     | `-` `!` `not` (unário)| direita         |
| 9     | chamada `f()`         | esquerda        |
