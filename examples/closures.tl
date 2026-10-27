# closures: a função interna "lembra" das variáveis de onde foi criada

fn contador(inicio) {
    let n = inicio;
    return fn() {
        n = n + 1;
        return n;
    };
}

let a = contador(0);
let b = contador(100);
a(); a();
print("a:", a());   # 3
print("b:", b());   # 101, não interfere no a

# funções de ordem superior
fn compoe(f, g) {
    return fn(x) { return f(g(x)); };
}

let dobro = fn(x) { return x * 2; };
let maisUm = fn(x) { return x + 1; };
let dobroDepoisMaisUm = compoe(maisUm, dobro);
print("compoe(maisUm, dobro)(5) =", dobroDepoisMaisUm(5));   # 11
